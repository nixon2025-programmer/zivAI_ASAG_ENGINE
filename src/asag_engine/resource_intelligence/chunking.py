import hashlib


def _stable_id(*parts: str) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8"))
    return h.hexdigest()


def chunk_document(doc_id, filename, file_type, pages, chunk_size=1200, overlap=200):
    chunks = []

    for page_number, text in pages:
        text = text.strip()
        start = 0
        n = len(text)

        while start < n:
            end = min(n, start + chunk_size)
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_id = _stable_id(doc_id, str(page_number), str(start))
                snippet = chunk_text[:300]

                chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "filename": filename,
                    "file_type": file_type,
                    "page_number": page_number,
                    "chunk_text": chunk_text,
                    "snippet": snippet,
                })

            if end == n:
                break

            start = max(0, end - overlap)

    return chunks