import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

def build_faiss_index(docs: List[Document], embed_model: str, base_url: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    embeddings = OllamaEmbeddings(model=embed_model, base_url=base_url)
    vs = FAISS.from_documents(docs, embeddings)
    vs.save_local(out_dir)

def load_faiss_index(embed_model: str, base_url: str, dir_path: str) -> FAISS:
    embeddings = OllamaEmbeddings(model=embed_model, base_url=base_url)
    return FAISS.load_local(dir_path, embeddings, allow_dangerous_deserialization=True)
