from django.db.models import Avg, Q
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from .models import StudentProfile
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
