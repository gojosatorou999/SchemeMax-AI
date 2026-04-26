import traceback
import pytesseract
from PIL import Image
from flask import current_app

def extract_text(image_path: str) -> str:
    """
    Extracts text from an image file using Tesseract OCR.
    """
    try:
        # Some environments (e.g. Windows) require setting the tesseract_cmd path explicitly.
        # This can be configured via environment variable if needed, but we try default first.
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        
        if not text.strip():
            return "No text extracted."
            
        return text.strip()
    except Exception as e:
        current_app.logger.error(f"OCR Error: {traceback.format_exc()}")
        return "No text extracted or OCR failed."
