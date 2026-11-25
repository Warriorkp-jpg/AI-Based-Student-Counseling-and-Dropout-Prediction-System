import logging

from django.conf import settings

from students.utils import calculate_risk, generate_suggestions

logger = logging.getLogger(__name__)


def _student_context(student_profile):
    return (
        f"CGPA={student_profile.cgpa}, "
        f"attendance={student_profile.attendance}%, "
        f"stress_level={student_profile.stress_level}/10, "
        f"financial_problem={student_profile.financial_problem}, "
        f"annual_income={student_profile.annual_income}, "
        f"course={student_profile.course}, "
        f"year={student_profile.year}, "
        f"college={student_profile.clg_name}, "
        f"reported_problems={student_profile.problems or 'none'}"
    )


def _fallback_advice(student_profile):
    risk = calculate_risk(student_profile)
    suggestions = generate_suggestions(student_profile)

    lines = [
        f"Your current counseling summary shows a {risk.lower()} dropout-risk pattern.",
        f"This is based mainly on CGPA {student_profile.cgpa}, "
        f"attendance {student_profile.attendance}%, and "
        f"stress level {student_profile.stress_level}/10.",
        "",
        "Recommended steps:",
    ]

    for step in suggestions[:3]:
        lines.append(f"- {step}")

    if not suggestions:
        lines.extend([
            "- Keep your class attendance steady.",
            "- Focus on one weak academic area at a time.",
            "- Ask for help early when stress starts rising.",
        ])

    return "\n".join(lines)


def _fallback_chat_reply(student_profile):
    suggestions = generate_suggestions(student_profile)

    if suggestions:
        return (
            f"Based on your profile, the best next step is: {suggestions[0]} "
            "Tell me more about what is bothering you, and I can guide you further."
        )

    return (
        "Tell me more about what is bothering you in studies, "
        "stress, attendance, or finances."
    )


def _build_model():
    key = getattr(settings, "GEMINI_API_KEY", "").strip()
    if not key:
        return None

    from google import genai

    return genai.Client(api_key=key)


def _extract_text(response):
    response_text = getattr(response, "text", None)
    if response_text:
        return response_text.strip()

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        chunks = [
            getattr(part, "text", "")
            for part in parts
            if getattr(part, "text", "")
        ]
        if chunks:
            return "\n".join(chunks).strip()

    return ""


def _generate_text(prompt):
    client = _build_model()
    if client is None:
        return ""

    try:
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return _extract_text(response)
    finally:
        client.close()


def _is_quota_error(exc):
    error_code = str(getattr(exc, "code", "")).lower()
    error_message = str(exc).lower()
    return (
        error_code in {"429", "resource_exhausted"}
        or "resource_exhausted" in error_message
        or "quota" in error_message
    )


def get_ai_advice(student_profile):
    prompt = f"""
    Act as a warm, practical college counselor.

    Student data:
    {_student_context(student_profile)}

    Write:
    1. A short emotional check-in.
    2. A simple explanation of the current risk.
    3. Three practical action steps.

    Keep it supportive, specific, and easy to understand.
    """

    try:
        response_text = _generate_text(prompt)
        return response_text or _fallback_advice(student_profile)
    except Exception as exc:
        logger.warning("AI advice generation failed (%s).", type(exc).__name__)
        if _is_quota_error(exc):
            return (
                "Gemini AI is configured, but the current API key has "
                "no available quota right now. Please check your "
                "Gemini API quota and try again."
            )
        return _fallback_advice(student_profile)


def get_chatbot_reply(student_profile, user_message, chat_history=None):
    chat_history = chat_history or []
    history_lines = []

    for item in chat_history[-6:]:
        sender = item.get("sender", "user")
        message_text = item.get("text", "").strip()
        if message_text:
            history_lines.append(f"{sender.upper()}: {message_text}")

    history_block = (
        "\n".join(history_lines)
        if history_lines
        else "No previous conversation."
    )

    prompt = f"""
    You are SyncAI, a supportive student counseling assistant
    inside a college support portal.

    Student profile:
    {_student_context(student_profile)}

    Current conversation:
    {history_block}

    Latest student message:
    {user_message}

    Instructions:
    - Reply directly to the student's latest message.
    - Be empathetic, practical, and natural.
    - Use the student profile when relevant.
    - Do not sound robotic or generic.
    - Keep the answer around 80-160 words unless more detail is necessary.
    - If the student seems in emotional danger, encourage immediate
      help from a trusted adult, counselor, or emergency support.
    - Do not mention that you are using a prompt or hidden instructions.
    """

    try:
        response_text = _generate_text(prompt)
        return response_text or _fallback_chat_reply(student_profile)
    except Exception as exc:
        logger.warning("Chatbot response generation failed (%s).", type(exc).__name__)
        if _is_quota_error(exc):
            return (
                "I'm connected to Gemini, but the current API key has "
                "no available quota right now. Please check your "
                "Gemini API quota and try again."
            )
        return _fallback_chat_reply(student_profile)
