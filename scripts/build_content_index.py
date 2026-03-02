
import os
import glob
import argparse
import logging
from typing import List

from langchain_core.documents import Document

from asag_engine.config import settings
from asag_engine.ingest.pdf_loaders import load_pdf
from asag_engine.ingest.chunking import chunk_docs
from asag_engine.index.vectorstore import build_faiss_index

log = logging.getLogger("asag.build_content_index")


def _infer_content_metadata(file_path: str) -> dict:
    base = os.path.basename(file_path)
    return {
        "doc_type": "content",
        "source_file": base,
        "source": file_path,
    }


def _load_and_chunk_pdf(path: str) -> List[Document]:
    docs = load_pdf(path)
    chunks = chunk_docs(docs)

    meta = _infer_content_metadata(path)
    for c in chunks:
        c.metadata = {**meta, **(c.metadata or {})}
    return chunks


def main():
    parser = argparse.ArgumentParser(description="Build content_faiss index from pdfs/textbooks PDFs.")
    parser.add_argument(
        "--content_dir",
        required=True,
        help="Directory containing PDF files (pdfs/textbooks). Example: data/raw/content",
    )
    parser.add_argument(
        "--out_dir",
        default="",
        help="Output index directory. Default: <INDEX_DIR>/content_faiss",
    )
    args = parser.parse_args()

    content_dir = args.content_dir
    if not os.path.isdir(content_dir):
        raise SystemExit(f"--content_dir not found or not a directory: {content_dir}")

    out_dir = args.out_dir.strip()
    if not out_dir:
        out_dir = os.path.join(settings.index_dir, "content_faiss")

    paths = sorted(glob.glob(os.path.join(content_dir, "*.pdf")))
    if not paths:
        raise SystemExit(f"No PDFs found in: {content_dir}")

    all_chunks: List[Document] = []
    for p in paths:
        chunks = _load_and_chunk_pdf(p)
        all_chunks.extend(chunks)
        log.info("Loaded %s -> %d chunks", p, len(chunks))

    os.makedirs(out_dir, exist_ok=True)
    log.info("Building FAISS index (%d chunks) -> %s", len(all_chunks), out_dir)

    build_faiss_index(
        docs=all_chunks,
        embed_model=settings.ollama_embed_model,
        base_url=settings.ollama_base_url,
        out_dir=out_dir,
    )

    log.info("Done. content_faiss index at: %s", out_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()