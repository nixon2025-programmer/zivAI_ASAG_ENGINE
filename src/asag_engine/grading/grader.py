import json
import logging
import re
from typing import Any, Dict, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from asag_engine.config import settings
from asag_engine.curriculum.coverage_tracker import CoverageTracker
from asag_engine.curriculum.curriculum_mapper import CurriculumMapper
from asag_engine.grading.schemas import (
    CoverageGap,
    CurriculumAlignment,
    GradeResult,
)
from asag_engine.rag.prompts import SYSTEM_GRADER, USER_GRADER_TEMPLATE
from asag_engine.rag.retriever import (
    DualRetriever,
    docs_to_context,
    normalize_paper_id,
)

log = logging.getLogger("asag.grader")




def _safe_json_load(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start:end + 1])
        raise ValueError(f"Model did not return valid JSON: {raw[:300]}")


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
    expr = expr.replace("×", "*").replace("÷", "/")
    expr = expr.replace("–", "-").replace("−", "-")

    if not re.fullmatch(r"[0-9\.\s\+\-\*\/\(\)]+", expr):
        return None

    try:
        return float(eval(expr, {"__builtins__": {}}, {}))
    except Exception:
        return None


def _solve_linear_x(question_text: str) -> Optional[float]:
    qt = (question_text or "").lower()
    if "x" not in qt or "=" not in qt:
        return None

    expr = qt.split(":", 1)[1].strip() if ":" in qt else qt
    expr = expr.replace(" ", "")
    expr = expr.replace("×", "*").replace("–", "-").replace("−", "-")
    expr = re.sub(r"(\d)(x)", r"\1*\2", expr)

    if not re.fullmatch(r"[0-9x\+\-\=\*\/\(\)\.]+", expr):
        return None

    try:
        left, right = expr.split("=", 1)

        def f(x: float) -> float:
            lx = left.replace("x", f"({x})")
            rx = right.replace("x", f"({x})")
            return float(eval(lx, {"__builtins__": {}}, {})) - \
                   float(eval(rx, {"__builtins__": {}}, {}))

        f0 = f(0.0)
        f1 = f(1.0)

        a = f1 - f0
        b = f0

        if abs(a) < 1e-12:
            return None

        return float(-b / a)

    except Exception:
        return None


def _ensure_feedback(obj: Dict[str, Any], max_score: float) -> None:
    fb = str(obj.get("feedback_short") or "").strip()
    if fb:
        obj["feedback_short"] = fb
        return

    score = float(obj.get("score_awarded") or 0.0)

    if score >= max_score and max_score > 0:
        obj["feedback_short"] = "Correct."
        obj["is_correct"] = True
    else:
        obj["feedback_short"] = "Incorrect."
        obj["is_correct"] = False


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default




class ASAGGrader:

    def __init__(self):
        self.llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
            format="json",
        )

        self.retriever = DualRetriever()
        self.mapper = CurriculumMapper()
        self.tracker = CoverageTracker()

        # persistent in-memory coverage
        self._coverage_history: Dict[str, Any] = {}



    def _attach_curriculum(self, result: GradeResult, question_text: str) -> GradeResult:
        try:
            alignment_raw = self.mapper.map_question(question_text)

            if isinstance(alignment_raw, dict):
                alignment = CurriculumAlignment.model_validate(alignment_raw)
            else:
                alignment = alignment_raw

            self._coverage_history = self.tracker.update_coverage(
                alignment_raw,
                result.score_awarded,
                result.max_score,
                self._coverage_history,
            )

            gaps_raw = self.tracker.analyse_gaps(self._coverage_history)

            gaps = []
            if isinstance(gaps_raw, list):
                for g in gaps_raw:
                    if isinstance(g, dict):
                        gaps.append(CoverageGap.model_validate(g))
                    elif isinstance(g, CoverageGap):
                        gaps.append(g)

            result.curriculum_alignment = alignment
            result.coverage_analysis = gaps

        except Exception as e:
            log.exception("Curriculum alignment failed: %s", e)

        return result



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

        prompt = USER_GRADER_TEMPLATE.format(
            paper_id=normalized_paper or "",
            question_id=question_id or "",
            question_text=question_text,
            student_answer=student_answer,
            max_marks=max_score,
            markscheme_found=str(not must_use_llm).lower(),
            markscheme_context=docs_to_context(ms_docs) if not must_use_llm else "",
            exam_context=docs_to_context(exam_docs) if not must_use_llm else "",
        )

        resp = self.llm.invoke([
            SystemMessage(content=SYSTEM_GRADER),
            HumanMessage(content=prompt),
        ])

        obj = _safe_json_load(resp.content)



        if max_score == 1.0:

            # Arithmetic
            correct = _safe_eval_arithmetic(question_text)

            if correct is not None:
                expected = int(correct) if float(correct).is_integer() else correct
                obj["expected_answer"] = str(expected)

                sval = _extract_last_number(student_answer)
                is_correct = sval is not None and abs(float(sval) - float(correct)) < 1e-9

                obj["is_correct"] = bool(is_correct)
                obj["score_awarded"] = 1.0 if is_correct else 0.0

            else:
                # Linear equation
                x = _solve_linear_x(question_text)
                if x is not None:
                    expected = int(x) if float(x).is_integer() else x
                    obj["expected_answer"] = f"x = {expected}"

                    sval = _extract_last_number(student_answer)
                    is_correct = sval is not None and abs(float(sval) - float(x)) < 1e-9

                    obj["is_correct"] = bool(is_correct)
                    obj["score_awarded"] = 1.0 if is_correct else 0.0



        obj["score_awarded"] = max(
            0.0,
            min(_to_float(obj.get("score_awarded"), 0.0), max_score),
        )

        obj["is_correct"] = bool(obj.get("is_correct", False))
        obj["expected_answer"] = str(obj.get("expected_answer") or "")
        obj["model_solution"] = str(obj.get("model_solution") or "")

        _ensure_feedback(obj, max_score)

        # ----------------------------------------------------
        # Build final result
        # ----------------------------------------------------

        result = GradeResult.model_validate({
            "expected_answer": obj["expected_answer"],
            "model_solution": obj["model_solution"],
            "score_awarded": obj["score_awarded"],
            "max_score": max_score,
            "feedback_short": obj["feedback_short"],
            "is_correct": obj["is_correct"],
            "mark_points_awarded": [],
            "missing_points": [],
            "sources": [],
        })

        return self._attach_curriculum(result, question_text)