from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import AssessmentAttempt, Assessment
from .schemas import TopicPerformance


class PerformanceEngine:

    @staticmethod
    def analyze_student(db: Session, student_id: str):
        results = (
            db.query(
                Assessment.topic_code,
                Assessment.topic_name,
                AssessmentAttempt.score_awarded,
                Assessment.max_score,
            )
            .join(Assessment, AssessmentAttempt.assessment_id == Assessment.id)
            .filter(AssessmentAttempt.student_id == student_id)
            .all()
        )

        if not results:
            return []

        topic_scores = {}

        for topic_code, topic_name, score, max_score in results:
            percent = (score / max_score) * 100

            if topic_code not in topic_scores:
                topic_scores[topic_code] = {
                    "topic_name": topic_name,
                    "scores": [],
                }

            topic_scores[topic_code]["scores"].append(percent)

        insights = []

        for topic_code, data in topic_scores.items():
            avg = sum(data["scores"]) / len(data["scores"])

            if avg >= 80:
                mastery = "High"
            elif avg >= 50:
                mastery = "Medium"
            else:
                mastery = "Low"

            insights.append(
                TopicPerformance(
                    topic_code=topic_code,
                    topic_name=data["topic_name"],
                    average_score=round(avg, 2),
                    mastery_level=mastery,
                )
            )

        return insights