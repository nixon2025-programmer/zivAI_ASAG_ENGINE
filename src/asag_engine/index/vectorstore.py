# src/asag_engine/index/vectorstore.py
import os
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings


def _embeddings(embed_model: str, base_url: str) -> OllamaEmbeddings:
    return OllamaEmbeddings(model=embed_model, base_url=base_url)


def build_faiss_index(docs: List[Document], embed_model: str, base_url: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    if not docs:
        return
    vs = FAISS.from_documents(docs, _embeddings(embed_model, base_url))
    vs.save_local(out_dir)


def load_faiss_index(embed_model: str, base_url: str, dir_path: str) -> FAISS:
    if not os.path.exists(dir_path):
        raise FileNotFoundError(f"FAISS index directory not found: {dir_path}")

    return FAISS.load_local(
        dir_path,
        _embeddings(embed_model, base_url),
        allow_dangerous_deserialization=True,
    )
