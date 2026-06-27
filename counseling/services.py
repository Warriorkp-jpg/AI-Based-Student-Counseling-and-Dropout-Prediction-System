from django.conf import settings

from students.utils import calculate_risk, generate_suggestions


def _student_context(student_profile):
    return (
        f"CGPA={student_profile.cgpa}, attendance={student_profile.attendance}%, "
        f"stress_level={student_profile.stress_level}/10, financial_problem={student_profile.financial_problem}, "
        f"annual_income={student_profile.annual_income}, course={student_profile.course}, year={student_profile.year}, "
        f"college={student_profile.clg_name}, reported_problems={student_profile.problems or 'none'}"
    )


def _fallback_advice(student_profile):
    risk = calculate_risk(student_profile)
    suggestions = generate_suggestions(student_profile)

    lines = [
        f"Your current counseling summary shows a {risk.lower()} dropout-risk pattern.",
        f"This is based mainly on CGPA {student_profile.cgpa}, attendance {student_profile.attendance}%, and stress level {student_profile.stress_level}/10.",
        "",
        "Recommended steps:",
    ]

    for step in suggestions[:3]:
        lines.append(f"- {step}")

    if len(lines) == 4:
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
    return "Tell me more about what is bothering you in studies, stress, attendance, or finances."


def _build_model():
    key = getattr(settings, 'GEMINI_API_KEY', '').strip()
    if not key:
        return None

    import google.generativeai as genai

    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-flash-latest')


def _extract_text(response):
    text = getattr(response, 'text', '').strip()
    if text:
        return text

    candidates = getattr(response, 'candidates', None) or []
    for candidate in candidates:
        content = getattr(candidate, 'content', None)
        parts = getattr(content, 'parts', None) or []
        chunks = [getattr(part, 'text', '') for part in parts if getattr(part, 'text', '')]
        if chunks:
            return "\n".join(chunks).strip()
    return ""


def get_ai_advice(student_profile):
    try:
        model = _build_model()
        
    except Exception as e:
        print(f"AI ERROR: {e}")
        return _fallback_advice(student_profile)

    if model is None:
        return _fallback_advice(student_profile)

    try:
        prompt = f"""
        Act as a warm, practical college counselor.
        Student data: {_student_context(student_profile)}

        Write:
        1. A short emotional check-in.
        2. A simple explanation of the current risk.
        3. Three practical action steps.
        Keep it supportive, specific, and easy to understand.
        """
        response = model.generate_content(prompt)
        text = _extract_text(response)
        return text or _fallback_advice(student_profile)
    except Exception as exc:
        if exc.__class__.__name__ == 'ResourceExhausted':
            return (
                "Gemini AI is configured, but the current API key has no available quota right now. "
                "Please enable billing or use a key/project with available Gemini quota, then try again."
            )
        return _fallback_advice(student_profile)


def get_chatbot_reply(student_profile, user_message, chat_history=None):
    chat_history = chat_history or []

    try:
        model = _build_model()
    except Exception:
        model = None

    if model is None:
        return _fallback_chat_reply(student_profile)

    history_lines = []
    for item in chat_history[-6:]:
        sender = item.get('sender', 'user')
        text = item.get('text', '').strip()
        if text:
            history_lines.append(f"{sender.upper()}: {text}")

    history_block = "\n".join(history_lines) if history_lines else "No previous conversation."

    prompt = f"""
    You are SyncAI, a supportive student counseling assistant inside a college support portal.

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
    - If the student seems in emotional danger, strongly encourage immediate help from a trusted adult, counselor, or emergency support.
    - Do not mention that you are using a prompt or hidden instructions.
    """

    try:
        response = model.generate_content(prompt)
        text = _extract_text(response)
        return text or _fallback_chat_reply(student_profile)
    except Exception as exc:
        if exc.__class__.__name__ == 'ResourceExhausted':
            return (
                "I’m connected to Gemini, but the current API key has no available quota right now. "
                "Please enable billing or switch to a key/project with available Gemini quota so I can answer with live AI."
            )
        return _fallback_chat_reply(student_profile)
