from typing import Dict, Any, Optional


class CoverageTracker:
    def update_coverage(
        self,
        alignment: Optional[Dict[str, Any]],
        score: float,
        max_score: float,
        history: Dict[str, Any],
    ) -> Dict[str, Any]:

        if alignment is None:
            return history

        topic = alignment.get("topic_code")
        if not topic:
            return history

        if topic not in history:
            history[topic] = {
                "attempted": 0,
                "correct": 0,
                "total_score": 0.0,
                "total_max": 0.0,
            }

        history[topic]["attempted"] += 1
        history[topic]["total_score"] += score
        history[topic]["total_max"] += max_score

        if score >= max_score:
            history[topic]["correct"] += 1

        return history

    def analyse_gaps(self, history: Dict[str, Any]):

        gaps = []

        for topic, stats in history.items():
            attempted = stats["attempted"]
            correct = stats["correct"]

            if attempted == 0:
                continue

            accuracy = correct / attempted

            if accuracy < 0.5:
                gaps.append(
                    {
                        "topic_code": topic,
                        "issue": "Low mastery",
                        "accuracy": round(accuracy, 2),
                        "recommendation": "Provide more practice questions.",
                    }
                )

        return gaps