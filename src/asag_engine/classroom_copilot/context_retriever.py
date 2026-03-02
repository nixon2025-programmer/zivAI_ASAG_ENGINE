from sqlalchemy.orm import Session
from asag_engine.resource_intelligence.service import ResourceIntelligenceService
from asag_engine.analytics.models import Assessment # your existing assessment model

class CopilotContextRetriever:

    def __init__(self, resource_service: ResourceIntelligenceService):
        self.resource_service = resource_service

    def retrieve(self, db: Session, topic: str, top_k: int = 5):
        # FAISS retrieval
        faiss_results = self.resource_service.search(db, topic, top_k)

        # Past assessments
        past_assessments = (
            db.query(Assessment)
            .filter(Assessment.topic_code.ilike(f"%{topic}%"))
            .limit(5)
            .all()
        )

        return {
            "faiss": faiss_results,
            "assessments": past_assessments,
        }