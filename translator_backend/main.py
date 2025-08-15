import io
import os
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException,Query
import threading
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image, ImageOps
import numpy as np
import pytesseract
import cv2
from deep_translator import GoogleTranslator

import config  # Your config.py should define TESSERACT_CMD, MAX_DIMENSION, SOURCE_LANG, DEFAULT_TARGET_LANG, CONFIDENCE_THRESHOLD

# Configure pytesseract
if config.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
if config.TESSDATA_PREFIX:
    os.environ["TESSDATA_PREFIX"] = config.TESSDATA_PREFIX



app = FastAPI(title="OCR + Translate API")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://image-livetranslator.netlify.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Global flag to stop the camera thread
stop_camera = False

def camera_loop(target_lang: str):
    global stop_camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return

    print("Press 'q' in the camera window to stop.")
    while not stop_camera:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # OCR
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        data = pytesseract.image_to_string(gray, lang=config.SOURCE_LANG)
        text = data.strip()
        translated = ""
        if text:
            try:
                translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            except:
                translated = "❌ Translation failed"

        # Overlay text on frame
        display_text = f"OCR: {text} | Translated: {translated}"
        cv2.putText(frame, display_text, (10,30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0,255,0), 2, cv2.LINE_AA)

        cv2.imshow("Live OCR Translator", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_camera = True
            break

    cap.release()
    cv2.destroyAllWindows()
    stop_camera = False
    print("Camera stopped.")

@app.get("/start-camera")
def start_camera(target_lang: str = Query(default=config.DEFAULT_TARGET_LANG)):
    global stop_camera
    if stop_camera:
        return {"status": "Camera already running"}
    # Run camera in a separate thread
    thread = threading.Thread(target=camera_loop, args=(target_lang,), daemon=True)
    thread.start()
    return {"status": "Camera started. Press 'q' in the window to stop."}






# -------------------------
# Data Models
# -------------------------
class Box(BaseModel):
    id: int
    text: str
    conf: float
    x: int
    y: int
    w: int
    h: int
    translated: Optional[str] = None

class OCRResponse(BaseModel):
    boxes: List[Box]
    width: int
    height: int

class TranslateRequest(BaseModel):
    text: str
    target_lang: str

# -------------------------
# Helpers
# -------------------------
def preprocess_for_ocr(pil_image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(pil_image)
    w, h = gray.size
    max_dim = config.MAX_DIMENSION
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        gray = gray.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    arr = np.array(gray)
    arr = cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 25, 10)
    return Image.fromarray(arr).convert("RGB")

# -------------------------
# OCR Endpoint
# -------------------------
@app.post("/ocr/", response_model=OCRResponse)
async def ocr_endpoint(
    file: UploadFile = File(...),
    target_lang: Optional[str] = Form(None),
    src_lang: Optional[str] = Form(None),
    bbox_conf_threshold: Optional[float] = Form(None)
):
    contents = await file.read()
    try:
        pil_img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

    proc = preprocess_for_ocr(pil_img)

    t_lang = src_lang or config.SOURCE_LANG
    target_lang = target_lang or config.DEFAULT_TARGET_LANG
    conf_threshold = float(bbox_conf_threshold) if bbox_conf_threshold else config.CONFIDENCE_THRESHOLD

    data = pytesseract.image_to_data(proc, lang=t_lang, output_type=pytesseract.Output.DICT)

    boxes = []
    for i, text in enumerate(data.get("text", [])):
        text = (text or "").strip()
        try:
            conf = float(data.get("conf", ["-1"])[i])
        except:
            conf = -1.0
        if not text or conf < conf_threshold:
            continue
        x, y, w, h = int(data.get("left", [0])[i]), int(data.get("top", [0])[i]), int(data.get("width", [0])[i]), int(data.get("height", [0])[i])
        # Translate
        translated = None
        try:
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        except:
            translated = None
        boxes.append(Box(id=i, text=text, conf=conf, x=x, y=y, w=w, h=h, translated=translated))

    return OCRResponse(boxes=boxes, width=proc.width, height=proc.height)

# -------------------------
# Translation Endpoint
# -------------------------
@app.post("/translate/")
def translate_text(req: TranslateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    try:
        translated = GoogleTranslator(source='auto', target=req.target_lang).translate(req.text)
        return {"original": req.text, "translatedText": translated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
