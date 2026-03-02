from sqlalchemy.orm import Session
from asag_engine.classroom_copilot.models import CopilotDraft
from asag_engine.classroom_copilot.schemas import CopilotRequest, CopilotEditRequest
from asag_engine.config import settings
import requests


class ClassroomCopilotService:

    def _ask_ollama(self, prompt: str) -> str:
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_chat_model,
                "prompt": prompt,
                "stream": False
            },
            timeout=settings.ollama_timeout,
        )
        response.raise_for_status()
        return response.json()["response"].strip()

    # -------------------------
    # GENERATE
    # -------------------------
    def generate(self, db: Session, req: CopilotRequest):

        prompt = f"""
You are a professional mathematics teacher.

Task Type: {req.task_type}
Topic: {req.topic}
Grade Level: {req.grade_level}

Instructions:
{req.instructions}

Generate structured content with mark allocation where relevant.
"""

        generated = self._ask_ollama(prompt)

        draft = CopilotDraft(
            task_type=req.task_type,
            topic=req.topic,
            grade_level=req.grade_level,
            content=generated,
            version=1,
        )

        db.add(draft)
        db.commit()
        db.refresh(draft)

        return {
            "draft_id": draft.id,
            "generated_content": draft.content,
            "citations": [],
            "version": draft.version,
        }

    # -------------------------
    # EDIT
    # -------------------------
    def edit(self, db: Session, req: CopilotEditRequest):

        draft = db.query(CopilotDraft).filter_by(id=req.draft_id).first()

        if not draft:
            raise ValueError("Draft not found")

        prompt = f"""
You are editing an existing draft.

Current Draft:
{draft.content}

Edit Instruction:
{req.edit_instruction}

Rewrite the full improved version.
"""

        updated_content = self._ask_ollama(prompt)

        draft.content = updated_content
        draft.version += 1

        db.commit()
        db.refresh(draft)

        return {
            "draft_id": draft.id,
            "generated_content": draft.content,
            "citations": [],
            "version": draft.version,
        }