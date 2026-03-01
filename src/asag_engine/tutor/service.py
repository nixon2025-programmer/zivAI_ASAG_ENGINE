import requests
from sqlalchemy.orm import Session
from asag_engine.config import settings
from asag_engine.analytics.models import AssessmentAttempt
from .prompt_builder import build_prompt


class TutorService:

    @staticmethod
    def _call_llm(prompt: str) -> str:
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.learning_plan_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=settings.ollama_timeout,
        )

        response.raise_for_status()
        return response.json()["response"].strip()

    @staticmethod
    def generate_response(
        db: Session,
        student_id: str,
        question_text: str,
        request_type: str,
        student_answer: str | None = None,
    ):

        # Pull last teacher feedback if exists
        last_attempt = (
            db.query(AssessmentAttempt)
            .filter(AssessmentAttempt.student_id == student_id)
            .order_by(AssessmentAttempt.attempt_date.desc())
            .first()
        )

        past_feedback = last_attempt.feedback if last_attempt else None

        prompt = build_prompt(
            request_type=request_type,
            question=question_text,
            student_answer=student_answer,
            past_feedback=past_feedback,
        )

        llm_response = TutorService._call_llm(prompt)

        return llm_response