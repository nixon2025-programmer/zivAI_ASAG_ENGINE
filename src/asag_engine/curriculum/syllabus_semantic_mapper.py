import json
import os
from typing import Dict, Any, List

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

from asag_engine.config import settings


BASE_DIR = os.path.dirname(__file__)
INDEX_PATH = os.path.join(BASE_DIR, "faiss_syllabus_index")


CURRICULUM_SYSTEM_PROMPT = """
You are a curriculum alignment engine.

You receive:
1) A student question.
2) Retrieved pdfs chunks.

Your task:
- Identify the best matching topic_code
- Identify topic_name
- Identify the most appropriate form level
- Provide confidence (0 to 1)
- Suggest 1–3 next topics if mastery is achieved.

Return ONLY valid JSON in this format:

{
  "topic_code": "",
  "topic_name": "",
  "form": "",
  "confidence": 0.0,
  "suggested_next_topics": []
}
"""


class SyllabusSemanticMapper:

    def __init__(self):
        embeddings = OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )

        self.vectorstore = FAISS.load_local(
            INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )

        self.llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
            format="json",
        )

    def map_question(self, question_text: str) -> Dict[str, Any]:
        """
        Semantic search pdfs index,
        then use LLM to decide best curriculum alignment.
        """

        docs = self.vectorstore.similarity_search(question_text, k=5)

        context = "\n\n".join([d.page_content for d in docs])

        user_prompt = f"""
Question:
{question_text}

Relevant pdfs sections:
{context}
"""

        response = self.llm.invoke([
            SystemMessage(content=CURRICULUM_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        try:
            return json.loads(response.content)
        except Exception:
            return {
                "topic_code": None,
                "topic_name": None,
                "form": None,
                "confidence": 0.0,
                "suggested_next_topics": [],
            }