import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    env: str = os.getenv("ENV", "dev")

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1")
    ollama_embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    top_k_markscheme: int = int(os.getenv("TOP_K_MARKSCHEME", "6"))
    top_k_exams: int = int(os.getenv("TOP_K_EXAMS", "4"))

    data_dir: str = os.getenv("DATA_DIR", "data")
    index_dir: str = os.getenv("INDEX_DIR", "data/indexes")

settings = Settings()
