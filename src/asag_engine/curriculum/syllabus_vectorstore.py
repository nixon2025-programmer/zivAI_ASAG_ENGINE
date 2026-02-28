import os
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from asag_engine.config import settings


def load_syllabus_index():
    path = os.path.join(settings.index_dir, "syllabus_faiss")

    embeddings = OllamaEmbeddings(
        model=settings.ollama_embed_model,
        base_url=settings.ollama_base_url
    )

    return FAISS.load_local(
        path,
        embeddings,
        allow_dangerous_deserialization=True
    )