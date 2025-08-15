import cv2
import pytesseract
from deep_translator import GoogleTranslator
import config  # SOURCE_LANG, DEFAULT_TARGET_LANG

# Global flag to stop
stop_camera = False

def live_ocr_translator(target_lang=config.DEFAULT_TARGET_LANG):
    """Live OCR translator using camera input.
    
    This function captures video from the default camera, performs OCR on each
    frame to extract text, translates the extracted text into a target language
    using Google Translator, and overlays both the original and translated text
    onto the video feed. The process continues until the user presses 'q', at which
    point the camera is stopped.
    
    Args:
        target_lang (str): The target language for translation, defaulting to
            `config.DEFAULT_TARGET_LANG`.
    """
    global stop_camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return

    print("Press 'q' to stop the camera")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # OCR
        try:
            text = pytesseract.image_to_string(gray, lang=config.SOURCE_LANG).strip()
        except:
            text = ""

        # Translate
        translated = ""
        if text:
            try:
                translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            except:
                translated = "❌ Translation failed"

        # Overlay original and translated text
        display_text = f"OCR: {text} | Translated: {translated}"
        # Split into lines if too long
        y0, dy = 30, 30
        for i, line in enumerate(display_text.split("|")):
            y = y0 + i*dy
            cv2.putText(frame, line.strip(), (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2, cv2.LINE_AA)

        cv2.imshow("Live OCR Translator", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_camera = True
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Camera stopped.")

# Example usage
if __name__ == "__main__":
    live_ocr_translator(target_lang="l")  # Change target_lang as needed
