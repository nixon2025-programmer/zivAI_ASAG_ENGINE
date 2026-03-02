import docx


def extract_docx(doc_id, filename, path):
    d = docx.Document(str(path))
    text = "\n".join(p.text for p in d.paragraphs if p.text.strip())

    return {
        "doc_id": doc_id,
        "filename": filename,
        "file_type": "docx",
        "pages": [(1, text)],
    }