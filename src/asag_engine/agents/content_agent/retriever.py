import os
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from asag_engine.index.vectorstore import load_faiss_index
from asag_engine.config import settings


class ContentRetriever:
    def __init__(self):
        self.dir_path = os.path.join(settings.index_dir, "content_faiss")
        self.vs = None
        if os.path.exists(self.dir_path):
            self.vs = load_faiss_index(settings.ollama_embed_model, settings.ollama_base_url, self.dir_path)

    def available(self) -> bool:
        return self.vs is not None

    def retrieve(self, query: str, k: int = 6) -> List[Document]:
        if not self.vs:
            return []
        return self.vs.similarity_search(query, k=k)


def docs_to_context(docs: List[Document], max_chars: int = 3500) -> str:
    parts = []
    total = 0
    for i, d in enumerate(docs, start=1):
        meta = d.metadata or {}
        slim_meta = {k: meta.get(k) for k in ("source_file", "page", "source") if k in meta}
        block = f"[{i}] {d.page_content}\nMETA: {slim_meta}\n"
        if total + len(block) > max_chars:
            remain = max_chars - total
            if remain > 0:
                parts.append(block[:remain])
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)


def docs_to_sources(docs: List[Document], limit: int = 3) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for d in docs[:limit]:
        meta = d.metadata or {}
        out.append(
            {
                "doc_type": "content_rag",
                "source_file": meta.get("source_file"),
                "metadata": {k: meta.get(k) for k in ("page", "source") if k in meta},
            }
        )
    return out