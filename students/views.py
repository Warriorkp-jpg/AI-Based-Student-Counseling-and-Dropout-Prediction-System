from django.db.models import Avg, Q
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from .models import (
    FeedbackAnnouncement,
    FeedbackConversation,
    FeedbackMessage,
    StudentProfile,
)
from django.contrib.auth.decorators import login_required
from .forms import StudentProfileForm
from .utils import calculate_risk, generate_suggestions
from django.contrib import messages
from .ai_features import (
    get_ai_tutor_reply,
    get_dropout_prediction_report,
    get_student_analysis_report,
    get_study_plan_report,
)
from .course_catalog import COURSE_CATALOG, get_course_curriculum


def _get_student_profile_or_redirect(request):
    """
    Shared guard for student-only feature pages.
    Returning the same redirect logic from one place keeps the
    feature views short and easier to understand.
    """
    if request.user.role != 'student':
        messages.info(request, "This page is available for student accounts.")
        return None, redirect('dashboard')

    student = StudentProfile.objects.filter(user=request.user).first()
    if not student:
        messages.warning(request, "Please complete your profile first.")
        return None, redirect('update_profile')

    return student, None


def _get_cached_ai_report(request, cache_key, generator):
    """
    Session caching helps us avoid wasting Gemini requests when a student
    opens the same page repeatedly.
    """
    cached_reports = request.session.get('student_ai_reports', {})
    if cache_key not in cached_reports:
        cached_reports[cache_key] = generator()
        request.session['student_ai_reports'] = cached_reports
        request.session.modified = True
    return cached_reports[cache_key]


def _profile_image_url(profile):
    """Avoid repeating the same profile-image check in each dashboard view."""
    return profile.profile_image.url if profile and profile.profile_image else None

@login_required
def dashboard(request):
    if request.user.role != 'student':
        return teacher_dashboard(request)
    
    if request.user.role =='admin':
        return student_detail(request)

    student = StudentProfile.objects.filter(user=request.user).first()

   
    if not student:
        messages.warning(request, "Please complete your profile first ⚠️")
        return redirect('update_profile')

    risk = calculate_risk(student)
    suggestions = generate_suggestions(student)

    return render(request, 'dashboard.html', {
        'student': student,
        'risk': risk,
        'suggestions': suggestions,
        'profile_image_url': student.profile_image.url if student.profile_image else None,
    })


@login_required
def teacher_dashboard(request):
    if request.user.role == 'student':
        messages.error(request, "This portal is only available for teachers.")
        return redirect('dashboard')
#  . strip () remove the spaaces in the URL patterns for search
    query = request.GET.get('q', '').strip()
    # fetching all students
    student_profiles_qs = StudentProfile.objects.select_related('user').order_by('user__username')

    if query:
        student_profiles_qs = student_profiles_qs.filter(
            Q(user__username__icontains=query)
            | Q(clg_name__icontains=query)
            | Q(roll_no__icontains=query)
            | Q(course__icontains=query)
            | Q(problems__icontains=query)
        )

    student_profiles = list(
        student_profiles_qs
    )

    student_rows = []
    risk_totals = {'High': 0, 'Medium': 0, 'Low': 0}

    for profile in student_profiles:
        risk = calculate_risk(profile)
        risk_totals[risk] += 1
        student_rows.append({
            'id': profile.id,
            'username': profile.user.username,
            'course': profile.get_course_display() if profile.course else 'Not set',
            'year': profile.year or 'N/A',
            'college': profile.clg_name or 'Not set',
            'roll_no': profile.roll_no or 'Not set',
            'cgpa': profile.cgpa,
            'attendance': profile.attendance,
            'stress_level': profile.stress_level,
            'risk': risk,
            'profile_image_url': profile.profile_image.url if profile.profile_image else None,
            'problems': profile.problems,
        })

    student_count = len(student_rows)
    flagged_students = [row for row in student_rows if row['risk'] == 'High']
    needs_attention = [row for row in student_rows if row['risk'] in ('High', 'Medium')]
    averages = StudentProfile.objects.aggregate(
        avg_cgpa=Avg('cgpa'),
        avg_attendance=Avg('attendance'),
        avg_stress=Avg('stress_level'),
    )

    return render(request, 'teacher_dashboard.html', {
        'student_count': student_count,
        'high_risk_count': risk_totals['High'],
        'medium_risk_count': risk_totals['Medium'],
        'low_risk_count': risk_totals['Low'],
        'avg_cgpa': round(averages['avg_cgpa'] or 0, 2),
        'avg_attendance': round(averages['avg_attendance'] or 0, 1),
        'avg_stress': round(averages['avg_stress'] or 0, 1),
        'flagged_students': flagged_students[:5],
        'needs_attention': needs_attention[:6],
        'student_rows': student_rows,
        'profile_image_url': None,
        'search_query': query,
    })


@login_required
def student_detail(request, student_id):
    if request.user.role == 'student':
        raise Http404("Student details are only available for teachers.")

    profile = StudentProfile.objects.select_related('user').filter(pk=student_id).first()
    if not profile:
        raise Http404("Student not found.")

    risk = calculate_risk(profile)
    suggestions = generate_suggestions(profile)

    return render(request, 'student_detail.html', {
        'student': profile,
        'risk': risk,
        'suggestions': suggestions,
        'profile_image_url': None,
        'student_profile_image_url': profile.profile_image.url if profile.profile_image else None,
        'search_query': request.GET.get('q', '').strip(),
    })
    
@login_required
def update_profile(request):
    if request.user.role != 'student':
        messages.info(request, "Teachers do not need a student profile.")
        return redirect('dashboard')

    student, created = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            # Clear cached AI reports so feature pages regenerate from the latest profile.
            request.session.pop('student_ai_reports', None)
            messages.success(request, "Profile updated successfully! ✅")
            return redirect('dashboard')
        else:

            messages.error(request, "Please correct the errors below.")
            print(form.errors) 
    else:
        form = StudentProfileForm(instance=student)

    return render(request, 'update_profile.html', {'form': form})


@login_required
def ai_tutor_dashboard(request):
    student, redirect_response = _get_student_profile_or_redirect(request)
    if redirect_response:
        return redirect_response

    chat_history = request.session.get('ai_tutor_chat', [])
    if not chat_history:
        chat_history = [{
            'sender': 'bot',
            'text': (
                f"Hello {request.user.username}, I’m your AI Tutor. "
                "Ask me about concepts, revision strategy, attendance recovery, or how to study better."
            ),
        }]

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        if not user_message:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Please enter a question before sending.'}, status=400)
            messages.error(request, "Please enter a question before sending.")
            return redirect('ai_tutor_dashboard')

        bot_reply = get_ai_tutor_reply(student, user_message, chat_history)
        chat_history.append({'sender': 'user', 'text': user_message})
        chat_history.append({'sender': 'bot', 'text': bot_reply})
        request.session['ai_tutor_chat'] = chat_history[-12:]
        request.session.modified = True

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'messages': [
                    {'sender': 'user', 'text': user_message},
                    {'sender': 'bot', 'text': bot_reply},
                ]
            })
        return redirect('ai_tutor_dashboard')

    return render(request, 'ai_tutor_dashboard.html', {
        'student': student,
        'chat_history': chat_history,
        'risk': calculate_risk(student),
        'suggestions': generate_suggestions(student),
        'profile_image_url': student.profile_image.url if student.profile_image else None,
    })


@login_required
def dropout_prediction_dashboard(request):
    student, redirect_response = _get_student_profile_or_redirect(request)
    if redirect_response:
        return redirect_response

    report = _get_cached_ai_report(
        request,
        'dropout_prediction_report',
        lambda: get_dropout_prediction_report(student),
    )

    return render(request, 'student_ai_feature.html', {
        'student': student,
        'feature_key': 'prediction',
        'feature_title': 'Dropout Prediction',
        'feature_icon': 'shield-alert',
        'feature_intro': 'See how your academic and wellness signals affect your current retention risk.',
        'feature_report': report,
        'risk': calculate_risk(student),
        'suggestions': generate_suggestions(student),
        'profile_image_url': student.profile_image.url if student.profile_image else None,
        'upcoming_features': [
            'Class trend forecasting',
            'Semester-wise risk timeline',
            'Mentor escalation suggestions',
        ],
    })


@login_required
def student_analysis_dashboard(request):
    student, redirect_response = _get_student_profile_or_redirect(request)
    if redirect_response:
        return redirect_response

    report = _get_cached_ai_report(
        request,
        'student_analysis_report',
        lambda: get_student_analysis_report(student),
    )

    return render(request, 'student_ai_feature.html', {
        'student': student,
        'feature_key': 'analysis',
        'feature_title': 'Student Analysis',
        'feature_icon': 'bar-chart-big',
        'feature_intro': 'Get an AI summary of your strengths, weak spots, and most useful next focus areas.',
        'feature_report': report,
        'risk': calculate_risk(student),
        'suggestions': generate_suggestions(student),
        'profile_image_url': student.profile_image.url if student.profile_image else None,
        'upcoming_features': [
            'Subject-wise insights',
            'Performance trend graphs',
            'Goal progress tracking',
        ],
    })


@login_required
def study_planner_dashboard(request):
    student, redirect_response = _get_student_profile_or_redirect(request)
    if redirect_response:
        return redirect_response

    report = _get_cached_ai_report(
        request,
        'study_planner_report',
        lambda: get_study_plan_report(student),
    )

    return render(request, 'student_ai_feature.html', {
        'student': student,
        'feature_key': 'planner',
        'feature_title': 'Study Planner',
        'feature_icon': 'calendar-check',
        'feature_intro': 'Use AI-generated weekly planning that matches your attendance, stress level, and study needs.',
        'feature_report': report,
        'risk': calculate_risk(student),
        'suggestions': generate_suggestions(student),
        'profile_image_url': student.profile_image.url if student.profile_image else None,
        'upcoming_features': [
            'Auto timetable builder',
            'Daily reminder system',
            'Exam countdown planning',
        ],
    })


@login_required
def course_hub(request):
    """Show curriculum data for students and a browseable course view for teachers."""
    if request.user.role == 'student':
        student = StudentProfile.objects.filter(user=request.user).first()
        if not student:
            messages.warning(request, "Please complete your profile first.")
            return redirect('update_profile')

        curriculum = get_course_curriculum(student.course or 'cse', student.year)
        return render(request, 'course_hub.html', {
            'curriculum': curriculum,
            'student': student,
            'is_teacher_view': False,
            'profile_image_url': _profile_image_url(student),
        })

    # Teachers can preview the same dummy API data for any course and year.
    course_code = request.GET.get('course', 'cse')
    if course_code not in COURSE_CATALOG:
        course_code = 'cse'

    try:
        selected_year = int(request.GET.get('year', 1))
    except (TypeError, ValueError):
        selected_year = 1

    curriculum = get_course_curriculum(course_code, selected_year)
    course_students = StudentProfile.objects.filter(course=course_code).select_related('user')
    return render(request, 'course_hub.html', {
        'curriculum': curriculum,
        'course_catalog': COURSE_CATALOG,
        'course_students': course_students,
        'is_teacher_view': True,
        'profile_image_url': None,
    })


def _load_feedback_conversation(conversation_id, user, is_teacher):
    """Fetch a feedback thread only when the logged-in user belongs to it."""
    conversations = FeedbackConversation.objects.select_related('teacher', 'student')
    if is_teacher:
        conversations = conversations.filter(teacher=user)
    else:
        conversations = conversations.filter(student=user)
    return conversations.filter(pk=conversation_id).first()


@login_required
def teacher_feedback_hub(request):
    """Teachers can broadcast course feedback or continue a private student thread."""
    if request.user.role == 'student':
        messages.info(request, "Feedback management is available for teachers.")
        return redirect('student_feedback_inbox')

    students = StudentProfile.objects.select_related('user').order_by('user__username')
    selected_conversation = None
    selected_id = request.GET.get('conversation') or request.POST.get('conversation_id')
    if selected_id:
        selected_conversation = _load_feedback_conversation(selected_id, request.user, True)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'announcement':
            title = request.POST.get('title', '').strip()
            body = request.POST.get('body', '').strip()
            target_course = request.POST.get('target_course', '').strip()
            if title and body:
                FeedbackAnnouncement.objects.create(
                    teacher=request.user,
                    title=title,
                    body=body,
                    target_course=target_course,
                )
                messages.success(request, "Feedback announcement sent.")
            else:
                messages.error(request, "Please add both a title and a message.")
            return redirect('teacher_feedback_hub')

        if action == 'start_conversation':
            student_id = request.POST.get('student_id')
            student_profile = students.filter(pk=student_id).first()
            if not student_profile:
                messages.error(request, "That student could not be found.")
                return redirect('teacher_feedback_hub')
            conversation, _ = FeedbackConversation.objects.get_or_create(
                teacher=request.user,
                student=student_profile.user,
            )
            return redirect(f"{request.path}?conversation={conversation.id}")

        if action == 'message' and selected_conversation:
            body = request.POST.get('body', '').strip()
            if body:
                FeedbackMessage.objects.create(
                    conversation=selected_conversation,
                    sender=request.user,
                    body=body,
                )
                selected_conversation.save(update_fields=['updated_at'])
            return redirect(f"{request.path}?conversation={selected_conversation.id}")

    conversations = FeedbackConversation.objects.filter(teacher=request.user).select_related('student').order_by('-updated_at')
    announcements = FeedbackAnnouncement.objects.filter(teacher=request.user)[:5]
    return render(request, 'teacher_feedback_hub.html', {
        'students': students,
        'conversations': conversations,
        'selected_conversation': selected_conversation,
        'announcements': announcements,
        'course_choices': StudentProfile.COURSE_CHOICES,
        'profile_image_url': None,
    })


@login_required
def student_feedback_inbox(request):
    """Students see announcements for their course and can reply in private teacher threads."""
    student, redirect_response = _get_student_profile_or_redirect(request)
    if redirect_response:
        return redirect_response

    selected_conversation = None
    selected_id = request.GET.get('conversation') or request.POST.get('conversation_id')
    if selected_id:
        selected_conversation = _load_feedback_conversation(selected_id, request.user, False)

    if request.method == 'POST' and selected_conversation:
        body = request.POST.get('body', '').strip()
        if body:
            FeedbackMessage.objects.create(
                conversation=selected_conversation,
                sender=request.user,
                body=body,
            )
            selected_conversation.save(update_fields=['updated_at'])
        return redirect(f"{request.path}?conversation={selected_conversation.id}")

    announcements = FeedbackAnnouncement.objects.filter(
        Q(target_course='') | Q(target_course=student.course)
    ).select_related('teacher')
    conversations = FeedbackConversation.objects.filter(student=request.user).select_related('teacher').order_by('-updated_at')
    return render(request, 'student_feedback_inbox.html', {
        'student': student,
        'announcements': announcements,
        'conversations': conversations,
        'selected_conversation': selected_conversation,
        'profile_image_url': _profile_image_url(student),
    })
