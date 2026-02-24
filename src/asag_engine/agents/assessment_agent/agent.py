import json
from typing import Any, Dict, List

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from asag_engine.config import settings
from asag_engine.agents.assessment_agent.schemas import (
    AssessmentGenerateRequest,
    AssessmentGenerateResponse,
)
from asag_engine.agents.assessment_agent.prompts import (
    SYSTEM_ASSESSMENT_GEN,
    USER_ASSESSMENT_GEN_TEMPLATE,
    USER_ASSESSMENT_REFINE_TEMPLATE,
)


def _safe_json_load(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start : end + 1])
        raise ValueError(f"Model did not return valid JSON. Output (first 500 chars): {raw[:500]}")


def _sum_points(questions: List[Dict[str, Any]]) -> float:
    total = 0.0
    for q in questions:
        try:
            total += float(q.get("points", 0.0))
        except Exception:
            pass
    return float(total)


def _renormalize_points(questions: List[Dict[str, Any]], target_total: float) -> List[Dict[str, Any]]:
    if not questions:
        return questions
    cur = _sum_points(questions)
    if cur <= 0:
        each = target_total / len(questions)
        for q in questions:
            q["points"] = float(each)
        return questions

    scale = target_total / cur
    running = 0.0
    for i, q in enumerate(questions):
        if i == len(questions) - 1:
            q["points"] = float(max(0.0, target_total - running))
        else:
            v = round(float(q.get("points", 0.0)) * scale, 2)
            q["points"] = float(v)
            running += float(v)
    return questions


def _coerce_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    try:
        return json.dumps(v, ensure_ascii=False).strip()
    except Exception:
        return str(v).strip()


def _norm_question_type(v: Any) -> str:
    s = (v or "").strip()
    if not s:
        return "short_answer"
    low = s.lower().replace("-", "_").replace(" ", "_")

    if low in {"short_answer", "shortanswer", "short"}:
        return "short_answer"
    if low in {"multiple_choice", "multiplechoice", "mcq"}:
        return "multiple_choice"
    if "multiple" in low and "choice" in low:
        return "multiple_choice"
    if low in {"structured"}:
        return "structured"
    if low in {"essay"}:
        return "essay"
    if low in {"true_false", "truefalse", "true/false", "boolean"} or ("true" in low and "false" in low):
        return "true_false"

    return "short_answer"


def _coerce_options(qtype: str, options: Any, correct_answer: str) -> List[Dict[str, Any]]:
    if qtype == "true_false":
        ca = (correct_answer or "").strip().lower()
        true_correct = ca in {"true", "t", "yes", "1"}
        return [{"text": "True", "isCorrect": bool(true_correct)}, {"text": "False", "isCorrect": bool(not true_correct)}]

    if not isinstance(options, list):
        return []

    out: List[Dict[str, Any]] = []
    for it in options:
        if isinstance(it, dict):
            text = _coerce_str(it.get("text"))
            if not text:
                continue
            out.append({"text": text, "isCorrect": bool(it.get("isCorrect", False))})
        else:
            text = _coerce_str(it)
            if not text:
                continue
            out.append({"text": text, "isCorrect": False})

    if qtype == "multiple_choice" and out:
        correct_count = sum(1 for o in out if o.get("isCorrect") is True)
        if correct_count == 0:
            out[0]["isCorrect"] = True
        elif correct_count > 1:
            first = True
            for o in out:
                if o.get("isCorrect") is True:
                    if first:
                        first = False
                    else:
                        o["isCorrect"] = False
    return out


def _sanitize_assessment_obj(obj: Dict[str, Any], req: AssessmentGenerateRequest) -> Dict[str, Any]:
    out = dict(obj or {})

    # top-level requireds
    out["name"] = _coerce_str(out.get("name") or req.name)
    out["description"] = _coerce_str(out.get("description") if out.get("description") is not None else req.description)
    out["type"] = _coerce_str(out.get("type") or req.type)
    out["maxScore"] = float(out.get("maxScore", req.maxScore))
    out["weight"] = float(out.get("weight", req.weight))
    out["dueDate"] = out.get("dueDate", req.dueDate)
    out["courseId"] = _coerce_str(out.get("courseId") or req.courseId)
    out["isAIEnhanced"] = bool(out.get("isAIEnhanced", req.isAIEnhanced))
    out["status"] = _coerce_str(out.get("status") or req.status)

    # questions
    qs = out.get("questions") or []
    if not isinstance(qs, list):
        qs = []

    fixed: List[Dict[str, Any]] = []
    for q in qs:
        if not isinstance(q, dict):
            continue

        qtype = _norm_question_type(q.get("questionType"))
        correct_answer = _coerce_str(q.get("correctAnswer"))

        fq = {
            "questionText": _coerce_str(q.get("questionText") or q.get("question") or ""),
            "questionType": qtype,
            "points": float(q.get("points") or 1),
            "correctAnswer": correct_answer,
            "attributes": q.get("attributes") if isinstance(q.get("attributes"), list) else [],
            "markScheme": _coerce_str(q.get("markScheme")),
            "rubric": _coerce_str(q.get("rubric")),
            "modelAnswer": _coerce_str(q.get("modelAnswer")),
        }
        fq["options"] = _coerce_options(qtype, q.get("options"), correct_answer)

        if len(fq["questionText"]) < 3:
            continue
        if fq["points"] <= 0:
            fq["points"] = 1.0

        fixed.append(fq)

    # if LLM returned empty questions, create minimal placeholders (still valid)
    if not fixed:
        n = int(req.numQuestions or 5)
        pts = float(req.maxScore) / max(1, n)
        for i in range(n):
            fixed.append(
                {
                    "questionText": f"Question {i+1} on {req.topic or req.subject or 'the topic'}.",
                    "questionType": "short_answer",
                    "points": float(pts),
                    "correctAnswer": "",
                    "options": [],
                    "attributes": [],
                    "markScheme": "",
                    "rubric": "",
                    "modelAnswer": "",
                }
            )

    out["questions"] = fixed
    _renormalize_points(out["questions"], float(out["maxScore"]))

    out["expectedTotal"] = float(out["maxScore"])
    out["answerKey"] = _coerce_str(out.get("answerKey"))[:800]
    out["notes"] = _coerce_str(out.get("notes"))[:400]

    sources = out.get("sources") if isinstance(out.get("sources"), list) else []
    sources = [{"doc_type": "ollama", "metadata": {"model": settings.ollama_chat_model}}] + sources
    out["sources"] = sources[:2]

    return out


class AssessmentAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0.2,
            format="json",
        )

    def _call_llm_json(self, system: str, user: str) -> Dict[str, Any]:
        resp = self.llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return _safe_json_load(resp.content)

    def generate(self, req: AssessmentGenerateRequest) -> AssessmentGenerateResponse:
        if not req.questions:
            user_prompt = USER_ASSESSMENT_GEN_TEMPLATE.format(
                subject=req.subject or "",
                grade=req.grade or "",
                topic=req.topic or "",
                difficulty=req.difficulty or "",
                atype=req.type,
                num_questions=req.numQuestions or 0,
                max_score=req.maxScore,
            )
            obj = self._call_llm_json(SYSTEM_ASSESSMENT_GEN, user_prompt)
        else:
            obj = req.model_dump()

        if req.regenerate:
            refine_prompt = USER_ASSESSMENT_REFINE_TEMPLATE.format(
                assessment_json=json.dumps(obj, ensure_ascii=False),
                instructions_json=json.dumps([r.model_dump() for r in req.regenerate], ensure_ascii=False),
            )
            obj = self._call_llm_json(SYSTEM_ASSESSMENT_GEN, refine_prompt)

        obj = _sanitize_assessment_obj(obj, req)
        return AssessmentGenerateResponse.model_validate(obj)