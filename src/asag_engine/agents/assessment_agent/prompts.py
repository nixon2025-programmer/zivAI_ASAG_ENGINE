SYSTEM_ASSESSMENT_GEN = """
You are a teacher assistant that generates assessments.
Return ONLY valid JSON.
Do not include markdown.
Follow the schema provided by the user instruction.
Keep explanations short.
"""

USER_ASSESSMENT_GEN_TEMPLATE = """
Generate an assessment.

CONTEXT:
- subject: {subject}
- grade: {grade}
- topic: {topic}
- difficulty: {difficulty}
- assessment_type: {atype}
- num_questions: {num_questions}
- max_score: {max_score}

REQUIREMENTS:
- Output JSON with fields:
  name, description, type, maxScore, weight, dueDate, courseId, isAIEnhanced, status,
  questions[], answerKey, expectedTotal, notes
- questions[] items must include:
  questionText, questionType, points, correctAnswer (if applicable), options (if applicable),
  markScheme, rubric, modelAnswer, attributes
- Ensure sum(points) == maxScore (or very close; adjust points to match maxScore exactly).
- Include a short answerKey (e.g. Q1: ..., Q2: ...).
"""

USER_ASSESSMENT_REFINE_TEMPLATE = """
Refine specific questions based on teacher feedback.

INPUT_ASSESSMENT_JSON:
{assessment_json}

REGENERATE_INSTRUCTIONS:
{instructions_json}

RULES:
- Only change questions at the specified questionIndex values.
- Keep the overall maxScore unchanged.
- Keep output JSON in the same structure.
- Return ONLY JSON.
"""