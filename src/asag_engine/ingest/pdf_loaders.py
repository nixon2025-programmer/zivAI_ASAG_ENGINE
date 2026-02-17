from langchain_community.document_loaders import PyMuPDFLoader
from typing import List
from langchain_core.documents import Document

def load_pdf(path: str) -> List[Document]:
    loader = PyMuPDFLoader(path)
    return loader.load()
