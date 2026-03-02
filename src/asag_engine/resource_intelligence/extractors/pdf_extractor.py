import fitz
from pathlib import Path


def extract_pdf(doc_id, filename, pdf_path, mindocr=None):
    doc = fitz.open(str(pdf_path))
    pages = []

    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        pages.append((i + 1, text))

    return {
        "doc_id": doc_id,
        "filename": filename,
        "file_type": "pdf",
        "pages": pages,
    }