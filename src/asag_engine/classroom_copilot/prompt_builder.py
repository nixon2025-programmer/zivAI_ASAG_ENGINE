def build_prompt(request, context):
    snippets = "\n\n".join(
        c["snippet"] for c in context["faiss"]["citations"]
    ) if context["faiss"]["citations"] else ""

    past_questions = "\n".join(
        a.title for a in context["assessments"]
    )

    prompt = f"""
You are an expert {request.grade_level} Mathematics teacher.

Topic: {request.topic}

Relevant School Material:
{snippets}

Previous School Assessments:
{past_questions}

Task:
Create a {request.task_type}.

Teacher Instructions:
{request.instructions or "Keep it structured and exam-oriented."}

Provide:
- Clear questions
- Mark allocation
- Structured format
- No introductory commentary
"""

    return prompt.strip()