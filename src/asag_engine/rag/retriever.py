import os
import re
from typing import List, Tuple, Dict, Any, Optional
from langchain_core.documents import Document

from asag_engine.index.vectorstore import load_faiss_index
from asag_engine.config import settings


def normalize_paper_id(paper_id: Optional[str]) -> str:
    p = (paper_id or "").strip().lower()
    if not p:
        return ""
    p = p.replace(".pdf", "")
    parts = p.split("-")
    if parts and parts[0].isdigit():
        parts = parts[1:]
    if len(parts) >= 2 and parts[-2:] == ["mark", "scheme"]:
        parts = parts[:-2]
    return "-".join(parts)


def _normalize_qid(qid: Optional[str]) -> List[str]:
    qid_raw = (qid or "").strip().lower()
    if not qid_raw:
        return []
    variants = {qid_raw}
    if qid_raw.startswith("q") and len(qid_raw) > 1:
        variants.add(qid_raw[1:])
    for v in list(variants):
        variants.add(re.sub(r"(\d)\(", r"\1 (", v))
    return [v for v in variants if v]


def _safe_filter_by_paper_id(
    docs: List[Document],
    normalized_paper_id: str,
    doc_type: Optional[str] = None,
) -> List[Document]:
    out: List[Document] = []
    for d in docs:
        meta = d.metadata or {}
        if doc_type and meta.get("doc_type") != doc_type:
            continue
        if normalized_paper_id:
            if "paper_id" in meta and str(meta.get("paper_id")).lower() != normalized_paper_id:
                continue
        out.append(d)
    return out


def _qid_hits(doc: Document, qid_variants: List[str]) -> bool:
    if not qid_variants:
        return False
    text = (doc.page_content or "").lower()
    return any(v in text for v in qid_variants)


def _prefer_question_hits(docs: List[Document], qid_variants: List[str]) -> List[Document]:
    hits, rest = [], []
    for d in docs:
        (hits if _qid_hits(d, qid_variants) else rest).append(d)
    return hits + rest


class DualRetriever:
    def __init__(self):
        ms_dir = f"{settings.index_dir}/markschemes_faiss"
        ex_dir = f"{settings.index_dir}/exams_faiss"

        if not os.path.exists(ms_dir) or not os.path.exists(ex_dir):
            raise RuntimeError(
                "Vector indexes not found. Build them first:\n"
                "python -m asag_engine.ingest.ingest_cli --exams_dir data/raw/exams --markschemes_dir data/raw/markschemes\n"
                "python -m asag_engine.index.build_indexes"
            )

        self.ms_vs = load_faiss_index(settings.ollama_embed_model, settings.ollama_base_url, ms_dir)
        self.exam_vs = load_faiss_index(settings.ollama_embed_model, settings.ollama_base_url, ex_dir)

    def retrieve(
        self,
        paper_id: Optional[str],
        question_id: Optional[str],
        question_text: str,
    ) -> Tuple[List[Document], List[Document], bool]:
        normalized_paper_id = normalize_paper_id(paper_id)

        # IMPORTANT: if no paper_id, do NOT retrieve random chunks
        if not normalized_paper_id:
            return [], [], False

        qid_variants = _normalize_qid(question_id)
        qid_query = " / ".join(qid_variants) if qid_variants else (question_id or "")
        query = f"{qid_query}\n{question_text}"

        ms_candidates = self.ms_vs.similarity_search(query, k=max(50, settings.top_k_markscheme * 10))
        ex_candidates = self.exam_vs.similarity_search(query, k=max(50, settings.top_k_exams * 10))

        ms_candidates = _safe_filter_by_paper_id(ms_candidates, normalized_paper_id, doc_type="markscheme")
        ex_candidates = _safe_filter_by_paper_id(ex_candidates, normalized_paper_id, doc_type="exam")

        ms_candidates = _prefer_question_hits(ms_candidates, qid_variants)
        ex_candidates = _prefer_question_hits(ex_candidates, qid_variants)

        markscheme_found = (
            any(_qid_hits(d, qid_variants) for d in ms_candidates)
            if qid_variants
            else (len(ms_candidates) > 0)
        )

        ms_docs = ms_candidates[: settings.top_k_markscheme]
        ex_docs = ex_candidates[: settings.top_k_exams]

        if not ms_docs:
            markscheme_found = False

        return ms_docs, ex_docs, markscheme_found


def docs_to_context(docs: List[Document], max_chars: int = 4500) -> str:
    parts = []
    total = 0
    for i, d in enumerate(docs, start=1):
        meta = d.metadata or {}
        slim_meta = {k: meta.get(k) for k in ("doc_type", "source_file", "paper_id", "page", "source") if k in meta}
        block = f"[{i}] {d.page_content}\nMETA: {slim_meta}\n"
        if total + len(block) > max_chars:
            remaining = max_chars - total
            if remaining > 0:
                parts.append(block[:remaining])
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)


def docs_to_sources(docs: List[Document], limit: int = 6) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for d in docs:
        meta = d.metadata or {}
        out.append(
            {
                "doc_type": meta.get("doc_type"),
                "source_file": meta.get("source_file"),
                "metadata": {k: meta.get(k) for k in ("paper_id", "page", "source") if k in meta},
            }
        )
        if len(out) >= limit:
            break
    return out
