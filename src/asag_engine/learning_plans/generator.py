import requests
from datetime import datetime, timedelta
from asag_engine.config import settings


class LearningPlanGenerator:

    @staticmethod
    def ask_ollama(prompt: str) -> str:
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.learning_plan_model,
                "prompt": prompt,
                "stream": False
            },
            timeout=settings.ollama_timeout
        )
        response.raise_for_status()
        return response.json()["response"].strip()

    @staticmethod
    def generate_resource(skill: str) -> str:
        prompt = f"""
        Create a concise HTML learning resource for Form 3 on {skill}.
        Include objective and worked example.
        Output HTML only.
        """
        return LearningPlanGenerator.ask_ollama(prompt)

    @staticmethod
    def generate_practice(skill: str) -> str:
        prompt = f"""
        Create short practice with worked example on {skill}.
        Output HTML only.
        """
        return LearningPlanGenerator.ask_ollama(prompt)