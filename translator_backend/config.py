# config.py
# Update these values to match your system and preferences

# Tesseract executable path (Windows example)
# e.g. r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# On Linux typically "/usr/bin/tesseract"
TESSERACT_CMD = r"D:\Program Files\tesseract.exe"

# If Tesseract can't find tessdata automatically, set this to the tessdata folder:
# e.g. r"D:\Program Files\Tesseract-OCR\tessdata"
TESSDATA_PREFIX = r"D:\Program Files\tessdata"

# Default OCR language(s) for Tesseract. For Tamil use 'tam' or 'tam+eng' for mixed text.
SOURCE_LANG = "tam"

# Default translation target (googletrans code). e.g. 'en' for English
DEFAULT_TARGET_LANG = "en"

# Confidence threshold to filter weak OCR results (0-100). Set low to show more boxes.
CONFIDENCE_THRESHOLD = 30

# Max width/height for resizing large uploads (speeds up processing)
MAX_DIMENSION = 1600
