
from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _safe_int(value: str, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _normalize_base_url(value: str) -> str:
    v = (value or "").strip().strip('"').strip("'")

    if not v:
        return ""

    # Prevent users from pasting Python code into .env
    if "os.getenv" in v or "{" in v or "}" in v:
        raise ValueError(
            "Invalid base URL in environment.\n"
            "Your .env must contain plain values only.\n"
            "Example:\n"
            "OLLAMA_BASE_URL=http://172.20.48.1:11434"
        )

    if not (v.startswith("http://") or v.startswith("https://")):
        v = "http://" + v

    return v.rstrip("/")


def _normalize_database_url(value: str) -> str:
    v = (value or "").strip().strip('"').strip("'")

    if not v:
        raise ValueError(
            "DATABASE_URL not set in environment.\n"
            "Example:\n"
            "postgresql+psycopg2://postgres:password@172.20.48.1:5432/asag_db"
        )

    if not v.startswith("postgresql"):
        raise ValueError(
            "DATABASE_URL must be a PostgreSQL connection string.\n"
            "Example:\n"
            "postgresql+psycopg2://postgres:password@host:5432/db"
        )

    return v

@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    env: str


    database_url: str


    ollama_base_url: str
    ollama_chat_model: str
    ollama_embed_model: str
    ollama_timeout: int
    learning_plan_model: str


    top_k_markscheme: int
    top_k_exams: int


    data_dir: str
    index_dir: str



def load_settings() -> Settings:

    host = os.getenv("HOST", "127.0.0.1").strip()
    port = _safe_int(os.getenv("PORT", "8000"), 8000)
    env = os.getenv("ENV", "dev").strip()


    raw_db = os.getenv("DATABASE_URL", "")
    database_url = _normalize_database_url(raw_db)


    raw_base = (
        os.getenv("MINDSPORE_LLM_URL", "").strip()
        or os.getenv("OLLAMA_BASE_URL", "").strip()
        or "http://127.0.0.1:11434"
    )

    ollama_base_url = _normalize_base_url(raw_base)

    if not ollama_base_url:
        raise ValueError("OLLAMA_BASE_URL resolved to empty value.")


    ollama_chat_model = os.getenv(
        "OLLAMA_CHAT_MODEL",
        "llama3.2:1b"
    ).strip()

    ollama_embed_model = os.getenv(
        "OLLAMA_EMBED_MODEL",
        "nomic-embed-text:latest"
    ).strip()

    learning_plan_model = os.getenv(
        "LEARNING_PLAN_MODEL",
        ollama_chat_model
    ).strip()

    ollama_timeout = _safe_int(
        os.getenv("OLLAMA_TIMEOUT", "60"),
        60
    )


    # Retrieval tuning

    top_k_markscheme = _safe_int(
        os.getenv("TOP_K_MARKSCHEME", "6"),
        6
    )

    top_k_exams = _safe_int(
        os.getenv("TOP_K_EXAMS", "4"),
        4
    )


    data_dir = os.getenv("DATA_DIR", "data").strip()
    index_dir = os.getenv("INDEX_DIR", "data/indexes").strip()


    return Settings(
        host=host,
        port=port,
        env=env,
        database_url=database_url,
        ollama_base_url=ollama_base_url,
        ollama_chat_model=ollama_chat_model,
        ollama_embed_model=ollama_embed_model,
        ollama_timeout=ollama_timeout,
        learning_plan_model=learning_plan_model,
        top_k_markscheme=top_k_markscheme,
        top_k_exams=top_k_exams,
        data_dir=data_dir,
        index_dir=index_dir,
    )


# Global singleton
settings = load_settings()