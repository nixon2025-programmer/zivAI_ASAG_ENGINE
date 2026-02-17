import json
import logging
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from asag_engine.config import settings
from asag_engine.rag.prompts import SYSTEM_GRADER, USER_GRADER_TEMPLATE
from asag_engine.rag.retriever import DualRetriever, docs_to_context, docs_to_sources
from asag_engine.grading.schemas import GradeResult

log = logging.getLogger("asag.grader")

class ASAGGrader:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
        )
        self.retriever = DualRetriever()

    def grade(self, question_text: str, student_answer: str, max_marks: float) -> GradeResult:
        query = f"{question_text}\nStudent answer: {student_answer}"
        ms_docs, exam_docs = self.retriever.retrieve(query)

        ms_context = docs_to_context(ms_docs)
        exam_context = docs_to_context(exam_docs)

        prompt = USER_GRADER_TEMPLATE.format(
            question_text=question_text,
            student_answer=student_answer,
            max_marks=max_marks,
            markscheme_context=ms_context,
            exam_context=exam_context,
        )

        resp = self.llm.invoke([
            SystemMessage(content=SYSTEM_GRADER),
            HumanMessage(content=prompt),
        ])

        # Strict JSON parse
        raw = resp.content.strip()
        try:
            obj = json.loads(raw)
        except Exception:
            # Try to recover: find first/last braces (basic)
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                obj = json.loads(raw[start:end+1])
            else:
                raise ValueError(f"Model did not return JSON. Output: {raw[:500]}")

        # Attach sources (retrieval provenance)
        obj["sources"] = docs_to_sources(ms_docs) + docs_to_sources(exam_docs)

        # Validate schema
        if "mark_points_awarded" in obj:
            for mp in obj["mark_points_awarded"]:
                if "point" in mp:
                    mp["point"] = str(mp["point"])

        result = GradeResult.model_validate(obj)

        # Enforce cap
        if result.score_awarded > result.max_score:
            result.score_awarded = result.max_score

        return result
