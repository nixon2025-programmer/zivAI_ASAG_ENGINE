
from __future__ import annotations

import os
from dataclasses import dataclass


def _normalize_base_url(value: str) -> str:
    v = (value or "").strip().strip('"').strip("'")
    if not v:
        return v

    # If someone mistakenly put python code in .env, fail loudly and clearly
    if "os.getenv" in v or "{" in v or "}" in v:
        raise ValueError(
            "Invalid base URL in environment. Your .env must contain plain values only.\n"
            "Example: OLLAMA_BASE_URL=http://172.20.48.1:11434"
        )

    # Add scheme if missing
    if not (v.startswith("http://") or v.startswith("https://")):
        v = "http://" + v

    return v.rstrip("/")


@dataclass(frozen=True)
class Settings:
    # Flask
    host: str
    port: int
    env: str

    # Ollama / LLM
    ollama_base_url: str
    ollama_chat_model: str
    ollama_embed_model: str

    # Retrieval tuning
    top_k_markscheme: int
    top_k_exams: int

    # Paths
    data_dir: str
    index_dir: str


def load_settings() -> Settings:
    host = os.getenv("HOST", "127.0.0.1").strip()
    port = int(os.getenv("PORT", "8000"))
    env = os.getenv("ENV", "dev").strip()

    # Prefer MINDSPORE_LLM_URL if set, else fall back to OLLAMA_BASE_URL
    raw_base = os.getenv("MINDSPORE_LLM_URL", "").strip() or os.getenv("OLLAMA_BASE_URL", "").strip()
    if not raw_base:
        raw_base = "http://127.0.0.1:11434"

    ollama_base_url = _normalize_base_url(raw_base)

    ollama_chat_model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:1b").strip()
    ollama_embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest").strip()

    top_k_markscheme = int(os.getenv("TOP_K_MARKSCHEME", "6"))
    top_k_exams = int(os.getenv("TOP_K_EXAMS", "4"))

    data_dir = os.getenv("DATA_DIR", "data").strip()
    index_dir = os.getenv("INDEX_DIR", "data/indexes").strip()

    return Settings(
        host=host,
        port=port,
        env=env,
        ollama_base_url=ollama_base_url,
        ollama_chat_model=ollama_chat_model,
        ollama_embed_model=ollama_embed_model,
        top_k_markscheme=top_k_markscheme,
        top_k_exams=top_k_exams,
        data_dir=data_dir,
        index_dir=index_dir,
    )


settings = load_settings()