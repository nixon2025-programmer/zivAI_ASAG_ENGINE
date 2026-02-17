from typing import List, Tuple, Dict, Any
from langchain_core.documents import Document

from asag_engine.index.vectorstore import load_faiss_index
from asag_engine.config import settings

class DualRetriever:
    def __init__(self):
        self.ms_vs = load_faiss_index(
            settings.ollama_embed_model, settings.ollama_base_url,
            f"{settings.index_dir}/markschemes_faiss"
        )
        self.exam_vs = load_faiss_index(
            settings.ollama_embed_model, settings.ollama_base_url,
            f"{settings.index_dir}/exams_faiss"
        )

    def retrieve(self, query: str) -> Tuple[List[Document], List[Document]]:
        ms_docs = self.ms_vs.similarity_search(query, k=settings.top_k_markscheme)
        exam_docs = self.exam_vs.similarity_search(query, k=settings.top_k_exams)
        return ms_docs, exam_docs

def docs_to_context(docs: List[Document]) -> str:
    parts = []
    for i, d in enumerate(docs, start=1):
        meta = d.metadata or {}
        parts.append(f"[{i}] {d.page_content}\nMETADATA: {meta}")
    return "\n\n".join(parts)

def docs_to_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    out = []
    for d in docs:
        meta = d.metadata or {}
        out.append({
            "doc_type": meta.get("doc_type"),
            "source_file": meta.get("source_file"),
            "metadata": meta,
        })
    return out
