# src/asag_engine/agents/assessment_agent/mindspore_client.py
from __future__ import annotations

from typing import Any, Dict, Optional
import json
import re
import requests

from asag_engine.config import settings


def _normalize_base_url(value: str) -> str:
    v = (value or "").strip().strip('"').strip("'")
    if not v:
        raise RuntimeError("LLM base_url is empty. Set OLLAMA_BASE_URL in .env.")
    if "os.getenv" in v or "{" in v or "}" in v:
        raise RuntimeError(
            "Invalid base_url detected. Your .env must contain plain values only.\n"
            "Example: OLLAMA_BASE_URL=http://172.20.48.1:11434"
        )
    if not (v.startswith("http://") or v.startswith("https://")):
        v = "http://" + v
    return v.rstrip("/")


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Best-effort extract JSON object from model output.
    """
    t = (text or "").strip()
    try:
        obj = json.loads(t)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    start = t.find("{")
    end = t.rfind("}")
    if start >= 0 and end > start:
        obj = json.loads(t[start : end + 1])
        if isinstance(obj, dict):
            return obj

    raise ValueError(f"Model did not return valid JSON. Output (first 400 chars): {t[:400]}")


class MindSporeLLM:
    def generate_json(self, system: str, user: str, schema_hint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError


class OllamaGateway(MindSporeLLM):
    """
    Uses your locally running Ollama (llama3.2:1b) as the agent LLM backend.
    """

    def __init__(self, base_url: str, model: str):
        self.base_url = _normalize_base_url(base_url)
        self.model = model

    def generate_json(self, system: str, user: str, schema_hint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        We instruct the model to return JSON only.
        Ollama /api/chat returns message.content as text. We parse.
        """
        schema_hint = schema_hint or {}

        sys = (system or "").strip()
        usr = (user or "").strip()

        # Keep schema small to avoid huge prompts
        schema_compact = json.dumps(schema_hint, ensure_ascii=False)[:2000]

        forced = (
            f"{sys}\n\n"
            "Return ONLY valid JSON. No markdown. No extra text.\n"
            f"If helpful, follow this schema hint: {schema_compact}\n\n"
            f"USER:\n{usr}\n"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": forced},
            ],
            "stream": False,
        }

        r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()

        content = ""
        if isinstance(data, dict):
            msg = data.get("message") or {}
            content = msg.get("content") or ""

        return _extract_json(content)


def build_llm_from_settings() -> MindSporeLLM:
    return OllamaGateway(
        base_url=settings.ollama_base_url,
        model=settings.ollama_chat_model,
    )