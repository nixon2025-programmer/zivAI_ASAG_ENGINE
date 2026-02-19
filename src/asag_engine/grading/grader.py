
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from asag_engine.config import settings
from asag_engine.rag.prompts import SYSTEM_GRADER, USER_GRADER_TEMPLATE
from asag_engine.rag.retriever import DualRetriever, docs_to_context, docs_to_sources, normalize_paper_id
from asag_engine.grading.schemas import GradeResult

log = logging.getLogger("asag.grader")


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


def _is_placeholder(x: Any) -> bool:
    if x is None:
        return True
    if isinstance(x, str) and x.strip().lower() in {"string", "n/a", "na", "null", ""}:
        return True
    return False


def _dedupe_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for s in sources:
        meta = s.get("metadata") or {}
        key = (s.get("doc_type"), s.get("source_file"), meta.get("paper_id"), meta.get("page"), meta.get("source"))
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def _normalize_points(points: Any, max_score: float) -> List[Dict[str, Any]]:
    if not isinstance(points, list):
        return []
    fixed: List[Dict[str, Any]] = []
    total = 0.0
    for p in points:
        if not isinstance(p, dict):
            continue
        point = str(p.get("point", "")).strip()
        just = str(p.get("justification", "")).strip()
        if _is_placeholder(point) or _is_placeholder(just):
            continue
        try:
            marks = float(p.get("marks", 0))
        except Exception:
            marks = 0.0
        marks = max(0.0, min(marks, max_score))
        if total + marks > max_score:
            marks = max(0.0, max_score - total)
        if marks <= 0:
            continue
        fixed.append({"point": point, "marks": marks, "justification": just})
        total += marks
        if total >= max_score:
            break
    return fixed


def _sum_points(points: List[Dict[str, Any]]) -> float:
    total = 0.0
    for p in points:
        try:
            total += float(p.get("marks", 0.0))
        except Exception:
            pass
    return total


def _extract_last_number(text: str) -> Optional[float]:
    nums = re.findall(r"-?\d+(?:\.\d+)?", text or "")
    if not nums:
        return None
    try:
        return float(nums[-1])
    except Exception:
        return None


def _safe_eval_arithmetic(expr: str) -> Optional[float]:
    expr = (expr or "").strip()
    expr = expr.replace("×", "*").replace("÷", "/").replace("–", "-").replace("−", "-")
    if not re.fullmatch(r"[0-9\.\s\+\-\*\/\(\)]+", expr):
        return None
    try:
        return float(eval(expr, {"__builtins__": {}}, {}))
    except Exception:
        return None


def _solve_linear_x(question_text: str) -> Optional[float]:
    qt = (question_text or "").lower()
    if "solve" not in qt or "for x" not in qt or "=" not in qt:
        return None

    expr = qt.split(":", 1)[1].strip() if ":" in qt else qt
    expr = expr.replace("×", "*").replace("–", "-").replace("−", "-").replace(" ", "")
    expr = re.sub(r"(\d)(x)", r"\1*\2", expr)

    if not re.fullmatch(r"[0-9x\+\-\=\*\/\(\)\.]+", expr):
        return None
    if any(tok in expr for tok in ["x*x", "xx", "^", "x2"]):
        return None

    left, right = expr.split("=", 1)

    def eval_side(s: str, xval: float) -> float:
        s2 = s.replace("x", f"({xval})")
        return float(eval(s2, {"__builtins__": {}}, {}))

    try:
        f0 = eval_side(left, 0) - eval_side(right, 0)
        f1 = eval_side(left, 1) - eval_side(right, 1)
        a = f1 - f0
        b = f0
        if abs(a) < 1e-12:
            return None
        return float(-b / a)
    except Exception:
        return None


def _solve_simul_linear_xy(question_text: str) -> Optional[Tuple[float, float]]:
    qt = (question_text or "").lower()
    if "=" not in qt or "x" not in qt or "y" not in qt:
        return None

    # must look like 2 equations
    if " and " not in qt and "," not in qt and "simultaneous" not in qt and "system" not in qt:
        return None

    expr = qt
    if ":" in expr:
        expr = expr.split(":", 1)[1].strip()

    expr = expr.replace("×", "*").replace("–", "-").replace("−", "-")
    expr = re.sub(r"\s+", " ", expr).strip()

    parts = re.split(r"\s+and\s+|,\s*", expr)
    eqs = [p.strip() for p in parts if "=" in p]
    if len(eqs) < 2:
        return None
    eq1, eq2 = eqs[0], eqs[1]

    def norm(eq: str) -> str:
        s = eq.replace(" ", "")
        s = re.sub(r"(\d)(x)", r"\1*\2", s)
        s = re.sub(r"(\d)(y)", r"\1*\2", s)
        return s

    eq1 = norm(eq1)
    eq2 = norm(eq2)

    if "^" in eq1 or "^" in eq2:
        return None
    if not re.fullmatch(r"[0-9xy\+\-\=\*\/\(\)\.]+", eq1):
        return None
    if not re.fullmatch(r"[0-9xy\+\-\=\*\/\(\)\.]+", eq2):
        return None

    def coeffs(eq: str) -> Optional[Tuple[float, float, float]]:
        left, right = eq.split("=", 1)

        def f(xv: float, yv: float) -> float:
            s = left.replace("x", f"({xv})").replace("y", f"({yv})")
            t = right.replace("x", f"({xv})").replace("y", f"({yv})")
            return float(eval(s, {"__builtins__": {}}, {})) - float(eval(t, {"__builtins__": {}}, {}))

        try:
            c = f(0, 0)
            ax = f(1, 0) - c
            by = f(0, 1) - c
            return (ax, by, -c)  # ax*x + by*y = k
        except Exception:
            return None

    c1 = coeffs(eq1)
    c2 = coeffs(eq2)
    if not c1 or not c2:
        return None

    a1, b1, k1 = c1
    a2, b2, k2 = c2

    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-12:
        return None

    x = (k1 * b2 - k2 * b1) / det
    y = (a1 * k2 - a2 * k1) / det
    return (float(x), float(y))


def _extract_xy_from_answer(student_answer: str) -> Tuple[Optional[float], Optional[float]]:
    sa = (student_answer or "").lower()
    mx = re.search(r"x\s*=\s*(-?\d+(?:\.\d+)?)", sa)
    my = re.search(r"y\s*=\s*(-?\d+(?:\.\d+)?)", sa)
    x = float(mx.group(1)) if mx else None
    y = float(my.group(1)) if my else None

    if x is None or y is None:
        nums = re.findall(r"-?\d+(?:\.\d+)?", sa)
        if len(nums) >= 2 and x is None and y is None:
            try:
                x = float(nums[0])
                y = float(nums[1])
            except Exception:
                pass
    return x, y


def _as_string(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, dict) or isinstance(x, list):
        try:
            return json.dumps(x, ensure_ascii=False)
        except Exception:
            return str(x)
    return str(x)


def _compact_llm_result(obj: Dict[str, Any], max_score: float) -> Dict[str, Any]:
    return {
        "expected_answer": _as_string(obj.get("expected_answer")),
        "is_correct": bool(obj.get("is_correct")),
        "score_awarded": float(obj.get("score_awarded") or 0.0),
        "max_score": float(obj.get("max_score") or max_score),
        "feedback_short": _as_string(obj.get("feedback_short")) or ("Correct." if bool(obj.get("is_correct")) else "Incorrect."),
        "model_solution": _as_string(obj.get("model_solution")),
        "mark_points_awarded": [],
        "missing_points": [],
        "sources": [],
    }


class ASAGGrader:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
            format="json",
        )
        self.retriever = DualRetriever()

    def grade(
        self,
        paper_id: Optional[str],
        question_id: Optional[str],
        question_text: str,
        student_answer: str,
        max_marks: float,
    ) -> GradeResult:
        max_score = float(max_marks)
        normalized_paper = normalize_paper_id(paper_id)

        if normalized_paper:
            ms_docs, exam_docs, markscheme_found = self.retriever.retrieve(
                paper_id=normalized_paper,
                question_id=question_id or "",
                question_text=question_text,
            )
        else:
            ms_docs, exam_docs, markscheme_found = [], [], False

        must_use_llm = (not normalized_paper) or (not markscheme_found)

        ms_context = docs_to_context(ms_docs)
        exam_context = docs_to_context(exam_docs)

        prompt = USER_GRADER_TEMPLATE.format(
            paper_id=normalized_paper or "",
            question_id=question_id or "",
            question_text=question_text,
            student_answer=student_answer,
            max_marks=max_score,
            markscheme_found="true" if (not must_use_llm and markscheme_found) else "false",
            markscheme_context=ms_context if (not must_use_llm and markscheme_found) else "",
            exam_context=exam_context if (not must_use_llm and markscheme_found) else "",
        )

        resp = self.llm.invoke([SystemMessage(content=SYSTEM_GRADER), HumanMessage(content=prompt)])
        obj = _safe_json_load(resp.content)

        obj["max_score"] = max_score
        obj["expected_answer"] = _as_string(obj.get("expected_answer"))
        obj["model_solution"] = _as_string(obj.get("model_solution"))

        # non-markscheme: verify deterministically where possible, but keep output compact
        if must_use_llm:
            obj["is_correct"] = bool(obj.get("is_correct")) if obj.get("is_correct") is not None else False
            obj["score_awarded"] = float(obj.get("score_awarded") or 0.0)
            obj["feedback_short"] = _as_string(obj.get("feedback_short"))

            # (A) arithmetic
            if max_score == 1.0:
                correct = _safe_eval_arithmetic(question_text)
                if correct is not None:
                    show = int(correct) if float(correct).is_integer() else correct
                    obj["expected_answer"] = str(show)
                    sval = _extract_last_number(student_answer)
                    obj["is_correct"] = (sval is not None and abs(float(correct) - float(sval)) < 1e-9)
                    obj["score_awarded"] = 1.0 if obj["is_correct"] else 0.0
                    obj["feedback_short"] = "Correct." if obj["is_correct"] else "Incorrect."
                    if not obj["model_solution"].strip():
                        obj["model_solution"] = f"Evaluate the expression to get {show}."

            # (B) solve for x
            if max_score == 1.0 and not obj["expected_answer"].strip():
                x = _solve_linear_x(question_text)
                if x is not None:
                    show = int(x) if float(x).is_integer() else x
                    obj["expected_answer"] = f"x = {show}"
                    sa = (student_answer or "").lower()
                    m = re.search(r"x\s*=\s*(-?\d+(?:\.\d+)?)", sa)
                    sval = float(m.group(1)) if m else _extract_last_number(sa)
                    obj["is_correct"] = (sval is not None and abs(float(sval) - float(x)) < 1e-9)
                    obj["score_awarded"] = 1.0 if obj["is_correct"] else 0.0
                    obj["feedback_short"] = "Correct." if obj["is_correct"] else "Incorrect."
                    if not obj["model_solution"].strip():
                        obj["model_solution"] = "Isolate x: move constants, then divide by the coefficient of x."

            # (C) simultaneous linear (x,y)
            sol = _solve_simul_linear_xy(question_text)
            if sol is not None:
                x, y = sol
                sx = int(x) if float(x).is_integer() else x
                sy = int(y) if float(y).is_integer() else y
                obj["expected_answer"] = f"x = {sx}, y = {sy}"
                ax, ay = _extract_xy_from_answer(student_answer)
                obj["is_correct"] = (
                    ax is not None and ay is not None and abs(float(ax) - float(x)) < 1e-9 and abs(float(ay) - float(y)) < 1e-9
                )
                if max_score == 1.0:
                    obj["score_awarded"] = 1.0 if obj["is_correct"] else 0.0
                    obj["feedback_short"] = "Correct." if obj["is_correct"] else "Incorrect."
                if not obj["model_solution"].strip():
                    obj["model_solution"] = "Eliminate one variable (add/subtract), solve for the other, then substitute back."

            # ensure consistent verdict
            if float(obj.get("score_awarded") or 0.0) >= max_score and max_score > 0:
                obj["is_correct"] = True
                obj["feedback_short"] = "Correct."
            elif float(obj.get("score_awarded") or 0.0) == 0.0:
                obj["is_correct"] = False
                obj["feedback_short"] = "Incorrect."

            # compact final output (no points/sources noise)
            return GradeResult.model_validate(_compact_llm_result(obj, max_score))

        # markscheme path (keep as-is, but bounded)
        obj["mark_points_awarded"] = _normalize_points(obj.get("mark_points_awarded"), max_score)
        obj["score_awarded"] = min(_sum_points(obj["mark_points_awarded"]), max_score)

        missing = obj.get("missing_points", [])
        if not isinstance(missing, list):
            missing = []
        obj["missing_points"] = [str(x) for x in missing if not _is_placeholder(x)][:20]

        sources = docs_to_sources(ms_docs, limit=4) + docs_to_sources(exam_docs, limit=2)
        obj["sources"] = _dedupe_sources(sources)

        if obj.get("score_awarded", 0.0) >= max_score and max_score > 0:
            obj["feedback_short"] = "Correct."
            obj["is_correct"] = True
        elif obj.get("score_awarded", 0.0) == 0.0:
            obj["feedback_short"] = "Incorrect."
            obj["is_correct"] = False

        # normalize optional fields for schema safety
        obj["expected_answer"] = _as_string(obj.get("expected_answer"))
        obj["model_solution"] = _as_string(obj.get("model_solution"))

        return GradeResult.model_validate(obj)
