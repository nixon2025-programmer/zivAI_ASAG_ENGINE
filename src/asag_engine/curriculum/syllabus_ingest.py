import json
from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parent
SYLLABUS_PATH = BASE_DIR / "syllabus.json"
OUTPUT_PATH = BASE_DIR / "syllabus_chunks.json"


def load_syllabus() -> Dict:
    if not SYLLABUS_PATH.exists():
        raise FileNotFoundError(f"Syllabus file not found at {SYLLABUS_PATH}")
    with open(SYLLABUS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def create_chunks(syllabus: Dict) -> List[Dict]:
    chunks = []

    for topic in syllabus.get("topics", []):
        topic_code = topic["topic_code"]
        topic_name = topic["topic_name"]

        for form, subtopics in topic.get("forms", {}).items():
            for subtopic in subtopics:
                text = f"""
Syllabus: {syllabus['syllabus_name']}
Topic: {topic_name}
Topic Code: {topic_code}
Form: {form}
Subtopic: {subtopic}
                """.strip()

                chunks.append({
                    "text": text,
                    "metadata": {
                        "syllabus_name": syllabus["syllabus_name"],
                        "topic_code": topic_code,
                        "topic_name": topic_name,
                        "form": form,
                        "subtopic": subtopic,
                    }
                })

    return chunks


def save_chunks(chunks: List[Dict]):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    print(f"✅ Saved {len(chunks)} syllabus chunks to {OUTPUT_PATH}")


def main():
    syllabus = load_syllabus()
    chunks = create_chunks(syllabus)
    save_chunks(chunks)


if __name__ == "__main__":
    main()