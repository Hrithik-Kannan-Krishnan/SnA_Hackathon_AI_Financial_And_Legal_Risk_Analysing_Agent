from __future__ import annotations

from pathlib import Path
from typing import List

from pypdf import PdfReader

def _extract_text_pypdf(path: str) -> str:
    r = PdfReader(path)
    parts: List[str] = []
    for page in r.pages:
        t = page.extract_text() or ""
        t = t.strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts)

def _ocr_pdf(path: str) -> str:
    # OCR fallback for scanned PDFs
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(path, dpi=250)
    parts = []
    for img in images[:20]:  # MVP cap pages
        parts.append(pytesseract.image_to_string(img))
    return "\n\n".join(parts)

def extract_pdf_text(path: str) -> str:
    path = str(Path(path))
    text = _extract_text_pypdf(path)
    if len(text.strip()) >= 200:
        return text
    # fallback OCR
    try:
        ocr = _ocr_pdf(path)
        return ocr
    except Exception:
        # if OCR fails, return whatever we got
        return text
