import json
from typing import Any, Dict, List, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from asag_engine.agents.content_agent.prompts import SYSTEM_CONTENT_GEN, USER_CONTENT_GEN_TEMPLATE
from asag_engine.agents.content_agent.retriever import ContentRetriever, docs_to_context, docs_to_sources
from asag_engine.agents.content_agent.schemas import ContentGenerateRequest, ContentGenerateResponse
from asag_engine.config import settings


def _safe_json_load(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        # try to extract first JSON object
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start : end + 1])
        raise ValueError(f"Model did not return valid JSON. Output (first 500 chars): {raw[:500]}")


def _cap_text(x: Any, n: int) -> str:
    s = str(x or "").strip()
    return s[:n] if s else ""


def _as_list_str(x: Any) -> List[str]:
    if isinstance(x, list):
        out = []
        for i in x:
            s = str(i).strip()
            if s:
                out.append(s)
        return out
    if isinstance(x, str) and x.strip():
        return [x.strip()]
    return []


def _parse_json_if_string(x: Any) -> Any:
    """
    Some models return arrays/objects as strings. Attempt to parse if so.
    Also tolerates single-quoted pseudo-json by doing a conservative replace
    only if json.loads fails.
    """
    if not isinstance(x, str):
        return x
    s = x.strip()
    if not s:
        return x
    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
        try:
            return json.loads(s)
        except Exception:
            # best-effort: convert Python-ish single quotes to JSON quotes
            # (not perfect, but helps with llama small models)
            try:
                s2 = s.replace("'", '"')
                return json.loads(s2)
            except Exception:
                return x
    return x


def _ensure_worked_examples(x: Any) -> List[Dict[str, str]]:
    x = _parse_json_if_string(x)
    if not isinstance(x, list):
        return []
    out: List[Dict[str, str]] = []
    for item in x[:6]:
        if isinstance(item, dict):
            q = _cap_text(item.get("question"), 220)
            a = _cap_text(item.get("solution"), 520)
            if q and a:
                out.append({"question": q, "solution": a})
    return out


def _ensure_revision_sheet(x: Any) -> List[Dict[str, str]]:
    x = _parse_json_if_string(x)
    if not isinstance(x, list):
        return []
    out: List[Dict[str, str]] = []
    for item in x[:10]:
        if isinstance(item, dict):
            kp = _cap_text(item.get("keyPoint"), 180)
            qp = _cap_text(item.get("quickPractice"), 220)
            if kp and qp:
                out.append({"keyPoint": kp, "quickPractice": qp})
    return out


def _ensure_slide_outline(x: Any) -> Dict[str, Any]:
    x = _parse_json_if_string(x)
    if not isinstance(x, dict):
        return {"bulletPoints": []}

    bps = x.get("bulletPoints")
    bps = _parse_json_if_string(bps)

    if not isinstance(bps, list):
        return {"bulletPoints": []}

    fixed: List[Dict[str, str]] = []
    for bp in bps[:12]:
        if isinstance(bp, dict):
            t = _cap_text(bp.get("text"), 140)
            b = _cap_text(bp.get("bulletPoint"), 180)
            if t and b:
                fixed.append({"text": t, "bulletPoint": b})

    return {"bulletPoints": fixed}


class ContentAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0.2,
            format="json",
        )
        self.retriever = ContentRetriever()

    def _call_llm_json(self, system: str, user: str) -> Dict[str, Any]:
        resp = self.llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return _safe_json_load(resp.content)

    def generate(self, req: ContentGenerateRequest) -> ContentGenerateResponse:
        rag_docs: List[Any] = []
        rag_ctx = ""

        # --- Optional RAG ---
        if req.useRag and self.retriever.available():
            q = f"{req.topic}\nGrade: {req.grade or ''}\nFocus: {', '.join(req.focusPoints or [])}"
            rag_docs = self.retriever.retrieve(q, k=6)
            rag_ctx = docs_to_context(rag_docs)

        user_prompt = USER_CONTENT_GEN_TEMPLATE.format(
            courseId=req.courseId,
            sourceResourceId=req.sourceResourceId or "",
            topic=req.topic,
            grade=req.grade or "",
            curriculumStandard=req.curriculumStandard or "",
            learningObjectives=json.dumps(req.learningObjectives or [], ensure_ascii=False),
            compressionLevel=req.compressionLevel,
            differentiation=req.differentiation,
            focusPoints=json.dumps(req.focusPoints or [], ensure_ascii=False),
            includeFlashcards=str(req.includeFlashcards).lower(),
            ragEvidence=rag_ctx or "",
        )

        obj = self._call_llm_json(SYSTEM_CONTENT_GEN, user_prompt)

        # ---- Hard normalize & enforce schema ----
        obj["courseId"] = req.courseId
        obj["sourceResourceId"] = req.sourceResourceId if req.sourceResourceId else None
        obj["topic"] = req.topic
        obj["grade"] = req.grade
        obj["curriculumStandard"] = req.curriculumStandard
        obj["learningObjectives"] = _as_list_str(obj.get("learningObjectives")) or (req.learningObjectives or [])
        obj["compressionLevel"] = req.compressionLevel
        obj["differentiation"] = req.differentiation

        # Required text fields
        obj["summary"] = _cap_text(obj.get("summary"), 900) or f"Summary of {req.topic}."
        obj["lessonNotes"] = _cap_text(obj.get("lessonNotes"), 2200) or f"Lesson notes for {req.topic}."

        # Structured fields
        obj["workedExamples"] = _ensure_worked_examples(obj.get("workedExamples"))
        if not obj["workedExamples"]:
            obj["workedExamples"] = [
                {"question": "Solve: 2x + 5 = 11", "solution": "2x = 6, so x = 3"},
                {"question": "Solve: x - 2 = 7", "solution": "x = 9"},
            ]

        obj["revisionSheet"] = _ensure_revision_sheet(obj.get("revisionSheet"))
        if not obj["revisionSheet"]:
            obj["revisionSheet"] = [
                {"keyPoint": "Order of operations (BODMAS)", "quickPractice": "Simplify: 3 + 2×5"},
                {"keyPoint": "Solving linear equations", "quickPractice": "Solve: 4x - 1 = 11"},
            ]

        obj["slideOutline"] = _ensure_slide_outline(obj.get("slideOutline"))
        if not obj["slideOutline"].get("bulletPoints"):
            obj["slideOutline"] = {
                "bulletPoints": [
                    {"text": "What is algebra?", "bulletPoint": "Using symbols to represent numbers"},
                    {"text": "Solving simple equations", "bulletPoint": "Do the same operation to both sides"},
                    {"text": "Practice", "bulletPoint": "Solve 3–5 equations as classwork"},
                ]
            }

        # Flashcards
        obj["includeFlashcards"] = bool(req.includeFlashcards)
        flashcards = _parse_json_if_string(obj.get("flashcards"))

        if not req.includeFlashcards:
            obj["flashcards"] = []
        else:
            if not isinstance(flashcards, list):
                flashcards = []
            fixed = []
            for fc in flashcards[:12]:
                if isinstance(fc, dict):
                    front = _cap_text(fc.get("front"), 120)
                    back = _cap_text(fc.get("back"), 220)
                    if front and back:
                        fixed.append({"front": front, "back": back})
            # fallback if model ignored flashcards
            if not fixed:
                fixed = [
                    {"front": "Define a variable.", "back": "A symbol (like x) that represents an unknown value."},
                    {"front": "What does solving an equation mean?", "back": "Finding the value of the variable that makes the equation true."},
                    {"front": "Inverse of +5?", "back": "Subtract 5."},
                    {"front": "Inverse of ×3?", "back": "Divide by 3."},
                    {"front": "What is BODMAS?", "back": "Order: Brackets, Orders, Division/Multiplication, Addition/Subtraction."},
                    {"front": "What is a coefficient?", "back": "The number multiplying a variable (e.g., 7 in 7x)."},
                ]
            obj["flashcards"] = fixed

        # RAG evidence
        obj["ragEvidence"] = _cap_text(rag_ctx, 1200) if (req.useRag and rag_ctx) else None

        # Sources
        sources = [{"doc_type": "ollama", "source_file": None, "metadata": {"model": settings.ollama_chat_model}}]
        if req.useRag and rag_docs:
            sources += docs_to_sources(rag_docs, limit=2)
        else:
            sources += [{"doc_type": "llm", "source_file": None, "metadata": {"reason": "Pure LLM generation (no RAG evidence used)"}}]
        obj["sources"] = sources[:3]

        return ContentGenerateResponse.model_validate(obj)