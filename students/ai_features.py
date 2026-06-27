from django.conf import settings

from students.utils import calculate_risk, generate_suggestions


def build_student_profile_summary(student_profile):
    """
    Keep the profile summary in one place so every AI feature uses
    the same student context.
    """
    return (
        f"Student profile: course={student_profile.course}, year={student_profile.year}, "
        f"cgpa={student_profile.cgpa}, attendance={student_profile.attendance}%, "
        f"stress_level={student_profile.stress_level}/10, financial_problem={student_profile.financial_problem}, "
        f"annual_income={student_profile.annual_income}, problems={student_profile.problems or 'none'}."
    )


def generate_ai_text(prompt, fallback_text):
    """
    Small wrapper around Gemini so the page views stay easy to read.
    If Gemini is unavailable or quota runs out, we return a safe fallback.
    """
    key = getattr(settings, 'GEMINI_API_KEY', '').strip()
    if not key:
        return fallback_text

    try:
        import google.generativeai as genai

        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)
        text = getattr(response, 'text', '').strip()
        return text or fallback_text
    except Exception:
        return fallback_text


def get_dropout_prediction_report(student_profile):
    risk = calculate_risk(student_profile)
    suggestions = generate_suggestions(student_profile)
    fallback = (
        f"Current dropout prediction: {risk} risk.\n\n"
        f"The strongest signals are CGPA {student_profile.cgpa}, attendance {student_profile.attendance}%, "
        f"and stress level {student_profile.stress_level}/10.\n\n"
        "Recommended next steps:\n- " + "\n- ".join(suggestions[:3])
    )

    prompt = f"""
    You are an academic risk analyst inside a student support portal.
    {build_student_profile_summary(student_profile)}
    Current rule-based risk level: {risk}.

    Write a short student-friendly report with:
    1. The current risk level.
    2. Why the risk looks this way.
    3. Three practical actions to reduce the risk.
    Keep it clear and supportive.
    """
    return generate_ai_text(prompt, fallback)


def get_student_analysis_report(student_profile):
    risk = calculate_risk(student_profile)
    suggestions = generate_suggestions(student_profile)
    fallback = (
        "Student analysis summary:\n"
        f"- Current risk: {risk}\n"
        f"- Strongest known data points: CGPA {student_profile.cgpa}, attendance {student_profile.attendance}%, "
        f"stress {student_profile.stress_level}/10\n"
        f"- Focus areas: {'; '.join(suggestions[:3])}"
    )

    prompt = f"""
    You are a student performance coach.
    {build_student_profile_summary(student_profile)}
    Current rule-based risk level: {risk}.

    Create a short analysis with:
    1. Strengths
    2. Areas that need attention
    3. Best next focus for this week
    Keep it practical and encouraging.
    """
    return generate_ai_text(prompt, fallback)


def get_study_plan_report(student_profile):
    suggestions = generate_suggestions(student_profile)
    fallback = (
        "Simple weekly study planner:\n"
        "- Day 1: Review your weakest subject for 45 minutes.\n"
        "- Day 2: Attend every class and rewrite missed notes.\n"
        "- Day 3: Solve one practice set and revise mistakes.\n"
        "- Day 4: Short stress break plus revision block.\n"
        "- Day 5: Ask a mentor or classmate about doubts.\n"
        "- Day 6: Revise and submit pending work.\n"
        "- Day 7: Check progress and plan next week.\n\n"
        f"Priority hints: {'; '.join(suggestions[:2])}"
    )

    prompt = f"""
    You are a study planner assistant.
    {build_student_profile_summary(student_profile)}

    Create a 7-day beginner-friendly study plan.
    Keep each day short, realistic, and specific.
    Include attendance, revision, and stress management when useful.
    """
    return generate_ai_text(prompt, fallback)


def get_ai_tutor_reply(student_profile, user_question, chat_history=None):
    chat_history = chat_history or []
    fallback = (
        "Here is a simple tutor answer based on your profile: "
        "break the problem into small parts, focus on your weakest subject first, "
        "and keep your class attendance steady while revising a little every day."
    )

    history_lines = []
    for item in chat_history[-6:]:
        text = item.get('text', '').strip()
        sender = item.get('sender', 'user')
        if text:
            history_lines.append(f"{sender.upper()}: {text}")

    prompt = f"""
    You are SyncAI Tutor, an academic support assistant for a college student.
    {build_student_profile_summary(student_profile)}

    Recent conversation:
    {' '.join(history_lines) if history_lines else 'No previous conversation.'}

    Student question:
    {user_question}

    Instructions:
    - Give a real, helpful tutor-style answer.
    - Keep the reply easy to understand for a beginner.
    - When relevant, connect the advice to attendance, CGPA, stress, or study consistency.
    - Keep the answer concise but useful.
    """
    return generate_ai_text(prompt, fallback)
