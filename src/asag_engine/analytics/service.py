from sqlalchemy.orm import Session
from .performance_engine import PerformanceEngine
from .intervention_engine import InterventionEngine
from .schemas import StudentInsight


class AnalyticsService:

    @staticmethod
    def student_insights(db: Session, student_id: str):

        performance = PerformanceEngine.analyze_student(db, student_id)

        risk, weak_topics = InterventionEngine.detect_risk(performance)

        recommendations = InterventionEngine.recommend(weak_topics)

        return StudentInsight(
            student_id=student_id,
            risk_level=risk,
            weak_topics=weak_topics,
            recommendations=recommendations,
        )