import os
import json
from typing import Dict, Any, List

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

from asag_engine.config import settings

BASE_DIR = os.path.dirname(__file__)
INDEX_PATH = os.path.join(BASE_DIR, "faiss_syllabus_index")


class CurriculumMapper:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
            format="json",
        )

        self.embeddings = OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )

        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(
                "Syllabus FAISS index not found. Run syllabus_ingest and syllabus_index first."
            )

        self.vectorstore = FAISS.load_local(
            INDEX_PATH,
            self.embeddings,
            allow_dangerous_deserialization=True,
        )

    def _retrieve_relevant_syllabus(self, question: str, k: int = 5):
        return self.vectorstore.similarity_search(question, k=k)

    def map_question(self, question: str) -> Dict[str, Any]:
        docs = self._retrieve_relevant_syllabus(question)

        syllabus_context = "\n\n".join(
            [f"{d.page_content}\nMetadata: {d.metadata}" for d in docs]
        )

        system_prompt = """
You are a curriculum alignment engine.

You MUST return STRICT JSON matching this exact structure:

{
  "syllabus_name": "string",
  "subject": "string",
  "grade_level": "string",
  "aligned_topics": [
    {
      "topic_code": "string",
      "topic_name": "string",
      "competency": "string",
      "cognitive_level": "string or null"
    }
  ],
  "coverage_gaps": [],
  "suggested_next_topics": ["string"],
  "best_match": {
    "subject": "string",
    "topic": "string",
    "subtopic": "string",
    "competency": "string",
    "confidence": 0.0
  }
}

Rules:
- aligned_topics MUST be full objects (NOT strings)
- best_match MUST contain ALL fields
- confidence must be between 0 and 1
- Return only JSON. No explanations.
"""

        user_prompt = f"""
QUESTION:
{question}

RETRIEVED SYLLABUS:
{syllabus_context}
"""

        response = self.llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )

        try:
            return json.loads(response.content)
        except Exception:
            return {
                "syllabus_name": None,
                "subject": None,
                "grade_level": None,
                "aligned_topics": [],
                "coverage_gaps": [],
                "suggested_next_topics": [],
                "best_match": None,
            }