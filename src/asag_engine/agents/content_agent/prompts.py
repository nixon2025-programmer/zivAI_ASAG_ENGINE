SYSTEM_CONTENT_GEN = """
You are ZivAI Content Agent.

You generate Mathematics/Academic content for teachers and students.

OUTPUT RULES:
- You MUST output VALID JSON only.
- JSON must match the required schema exactly.
- No markdown. No extra keys unless harmless.
- Keep content concise but useful.
- Use the requested compressionLevel: brief | medium | detailed.
- If includeFlashcards=false, return flashcards as [].

RAG RULES:
- If RAG_EVIDENCE is provided, use it as factual grounding.
- If RAG_EVIDENCE is empty, generate from general knowledge.
"""

USER_CONTENT_GEN_TEMPLATE = """
courseId: {courseId}
sourceResourceId: {sourceResourceId}
topic: {topic}
grade: {grade}
curriculumStandard: {curriculumStandard}
learningObjectives: {learningObjectives}
compressionLevel: {compressionLevel}
differentiation: {differentiation}
focusPoints: {focusPoints}
includeFlashcards: {includeFlashcards}

RAG_EVIDENCE (may be empty):
{ragEvidence}

Return JSON with:
- summary
- lessonNotes
- workedExamples (at least 2 examples)
- revisionSheet (key points + quick practice)
- slideOutline (bullet slide plan)
- flashcards (only if includeFlashcards=true)
"""