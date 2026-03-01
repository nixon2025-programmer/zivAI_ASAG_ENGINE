class InterventionEngine:

    @staticmethod
    def detect_risk(topic_performances):
        weak_topics = [
            t.topic_code for t in topic_performances
            if t.mastery_level == "Low"
        ]

        if len(weak_topics) >= 3:
            risk = "High"
        elif len(weak_topics) >= 1:
            risk = "Medium"
        else:
            risk = "Low"

        return risk, weak_topics

    @staticmethod
    def recommend(weak_topics):
        return [
            f"Provide remedial exercises for {topic}"
            for topic in weak_topics
        ]