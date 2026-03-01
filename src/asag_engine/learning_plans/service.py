from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from asag_engine.analytics.performance_engine import PerformanceEngine
from asag_engine.analytics.intervention_engine import InterventionEngine
from .schemas import LearningPlanResponse, LearningPlanMeta
from .generator import LearningPlanGenerator


class LearningPlanService:

    @staticmethod
    def generate_plan(db: Session, student_id: str):

        performance = PerformanceEngine.analyze_student(db, student_id)
        risk, weak_topics = InterventionEngine.detect_risk(performance)
        recommendations = InterventionEngine.recommend(weak_topics)

        if not performance:
            raise ValueError("No performance data available.")

        avg_mastery = sum(p.average_score for p in performance) / len(performance)
        target = min(avg_mastery + 20, 95)

        start = datetime.utcnow()
        end = start + timedelta(days=60)

        # Generate content only for weak topics
        for topic in weak_topics:
            LearningPlanGenerator.generate_resource(topic)
            LearningPlanGenerator.generate_practice(topic)

        return LearningPlanResponse(
            success=True,
            plan_id=f"pln_{start.strftime('%Y%m')}_{student_id}",
            student_id=student_id,
            plan_meta=LearningPlanMeta(
                status="active",
                start_date=start.strftime("%Y-%m-%d"),
                end_date=end.strftime("%Y-%m-%d"),
                mastery_now=round(avg_mastery, 1),
                mastery_target=round(target, 1)
            ),
            weak_topics=weak_topics,
            recommendations=recommendations
        )