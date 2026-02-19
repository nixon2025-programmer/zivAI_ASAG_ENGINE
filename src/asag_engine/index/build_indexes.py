# src/asag_engine/index/build_indexes.py
import os
import logging
from typing import List, Dict, Any

import orjson
from langchain_core.documents import Document

from asag_engine.config import settings
from asag_engine.index.vectorstore import build_faiss_index

log = logging.getLogger("asag.index")


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, "rb") as f:
        for line in f:
            if line.strip():
                records.append(orjson.loads(line))
    return records


def _to_docs(records: List[Dict[str, Any]]) -> List[Document]:
    docs: List[Document] = []
    for r in records:
        docs.append(Document(page_content=r["text"], metadata=r.get("metadata", {})))
    return docs


def main():
    processed_dir = os.path.join(settings.data_dir, "processed")
    exams_jsonl = os.path.join(processed_dir, "exams.jsonl")
    ms_jsonl = os.path.join(processed_dir, "markschemes.jsonl")

    exams = _to_docs(_read_jsonl(exams_jsonl))
    ms = _to_docs(_read_jsonl(ms_jsonl))

    exams_out = os.path.join(settings.index_dir, "exams_faiss")
    ms_out = os.path.join(settings.index_dir, "markschemes_faiss")

    build_faiss_index(exams, settings.ollama_embed_model, settings.ollama_base_url, exams_out)
    build_faiss_index(ms, settings.ollama_embed_model, settings.ollama_base_url, ms_out)

    log.info(f"Saved exams index -> {exams_out}")
    log.info(f"Saved markschemes index -> {ms_out}")


if __name__ == "__main__":
    main()
