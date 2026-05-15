"""
services/ocr.py — OCR text extraction with graceful fallback.

Tesseract is a system binary that is not available on Vercel's serverless
environment. We catch the ImportError / runtime errors and return a friendly
message so the rest of the app continues to work.
"""
import traceback

_TESSERACT_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    # Quick smoke-test: if tesseract binary is missing this raises
    pytesseract.get_tesseract_version()
    _TESSERACT_AVAILABLE = True
except Exception:
    pass


def extract_text(image_path: str) -> str:
    """
    Extracts text from an image file using Tesseract OCR.
    Returns a helpful message if Tesseract is unavailable (e.g. Vercel).
    """
    if not _TESSERACT_AVAILABLE:
        return (
            "OCR is not available in this deployment environment. "
            "Please paste your document text manually in the text field below."
        )

    try:
        from flask import current_app
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)

        if not text.strip():
            return "No text extracted."

        return text.strip()
    except Exception as e:
        try:
            from flask import current_app
            current_app.logger.error(f"OCR Error: {traceback.format_exc()}")
        except Exception:
            pass
        return "No text extracted or OCR failed."
