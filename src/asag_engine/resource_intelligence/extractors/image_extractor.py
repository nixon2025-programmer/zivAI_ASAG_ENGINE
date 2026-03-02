def extract_image_with_mindocr(doc_id, filename, image_path, mindocr):
    result = mindocr.ocr_image(image_path)

    text = ""
    if "stdout" in result:
        text = result["stdout"]

    return {
        "doc_id": doc_id,
        "filename": filename,
        "file_type": "image",
        "pages": [(1, text)],
    }