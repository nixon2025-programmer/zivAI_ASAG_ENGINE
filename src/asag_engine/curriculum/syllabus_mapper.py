from typing import Dict, Any
from asag_engine.curriculum.syllabus_vectorstore import load_syllabus_index


class CurriculumMapper:

    def __init__(self):
        self.vs = load_syllabus_index()

    def map_question(self, question_text: str) -> Dict[str, Any]:
        """
        Uses semantic similarity to align a question
        to the most relevant syllabus subtopic.
        """

        docs = self.vs.similarity_search(question_text, k=1)

        if not docs:
            return {
                "aligned_topics": [],
                "best_match": None,
                "coverage_gaps": [],
                "grade_level": None,
                "subject": None,
                "suggested_next_topics": [],
                "syllabus_name": None,
            }

        best = docs[0]
        meta = best.metadata or {}

        return {
            "aligned_topics": [meta.get("topic_name")],
            "best_match": meta.get("subtopic"),
            "coverage_gaps": [],
            "grade_level": meta.get("form"),
            "subject": meta.get("subject"),
            "suggested_next_topics": [],
            "syllabus_name": meta.get("syllabus_name"),
            "confidence": 0.85,
        }