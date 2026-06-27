from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from students.models import StudentProfile
from students.utils import calculate_risk, generate_suggestions
from .services import get_ai_advice, get_chatbot_reply
from django.contrib.auth.decorators import login_required

@login_required
def ai_counseling_dashboard(request):
    if request.user.role != 'student':
        messages.info(request, "AI counseling is available only for student accounts.")
        return redirect('dashboard')

    profile = StudentProfile.objects.filter(user=request.user).first()
    if not profile:
        messages.warning(request, "Please complete your profile first.")
        return redirect('update_profile')

    chat_history = request.session.get('ai_counseling_chat', [])

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        if not user_message:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Please enter a message before sending.'}, status=400)
            messages.error(request, "Please enter a message before sending.")
            return redirect('ai_counseling_dashboard')

        bot_reply = get_chatbot_reply(profile, user_message, chat_history)
        chat_history.append({'sender': 'user', 'text': user_message})
        chat_history.append({'sender': 'bot', 'text': bot_reply})
        request.session['ai_counseling_chat'] = chat_history[-12:]
        request.session.modified = True

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'messages': [
                    {'sender': 'user', 'text': user_message},
                    {'sender': 'bot', 'text': bot_reply},
                ]
            })
        return redirect('ai_counseling_dashboard')

    ai_advice = get_ai_advice(profile)
    risk = calculate_risk(profile)
    suggestions = generate_suggestions(profile)

    if not chat_history:
        chat_history = [{
            'sender': 'bot',
            'text': (
                f"Hello {request.user.username}. I reviewed your profile and your current risk level looks {risk.lower()}. "
                "Ask me about attendance, stress, study plans, or financial pressure."
            ),
        }]

    return render(request,'ai_counseling_dashboard.html',{
        'advice': ai_advice,
        'student': profile,
        'risk': risk,
        'suggestions': suggestions,
        'chat_history': chat_history,
        'profile_image_url': profile.profile_image.url if profile.profile_image else None,
    })
    
