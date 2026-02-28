import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document

BASE_DIR = Path(__file__).resolve().parent
CHUNKS_PATH = BASE_DIR / "syllabus_chunks.json"
INDEX_PATH = BASE_DIR / "faiss_syllabus_index"


def load_chunks():
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError("Run syllabus_ingest first.")
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_index(chunks):
    docs = [
        Document(page_content=c["text"], metadata=c["metadata"])
        for c in chunks
    ]

    from langchain_community.embeddings import OllamaEmbeddings

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text:latest",
        base_url="http://172.20.48.1:11434"
    )
    #embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

    print("🔄 Creating embeddings...")
    vectorstore = FAISS.from_documents(docs, embeddings)

    print("💾 Saving FAISS index...")
    vectorstore.save_local(str(INDEX_PATH))

    print(f"✅ Index saved at {INDEX_PATH}")


def main():
    chunks = load_chunks()
    build_index(chunks)


if __name__ == "__main__":
    main()