def build_prompt(
    request_type: str,
    question: str,
    student_answer: str | None,
    past_feedback: str | None,
) -> str:

    base_rules = """
You are a professional mathematics tutor.
STRICT RULES:
- Never reveal the final answer.
- Provide guidance only.
- Encourage student thinking.
- If giving steps, stop before the final numeric answer.
- Use a supportive tone.
"""

    if request_type == "explain":
        return f"""{base_rules}

Explain the following question clearly and simply:

Question:
{question}
"""

    if request_type == "hint":
        return f"""{base_rules}

Provide a helpful hint for this question WITHOUT solving it:

Question:
{question}
"""

    if request_type == "step_by_step":
        return f"""{base_rules}

Provide step-by-step guidance but do NOT reveal the final answer.

Question:
{question}
"""

    if request_type == "feedback":
        return f"""{base_rules}

The student answered:
{student_answer}

Past teacher feedback:
{past_feedback}

Provide coaching feedback explaining:
- What went wrong
- What concept needs review
- What to try next

Do not provide the final answer.
"""

    raise ValueError("Invalid tutor request type")