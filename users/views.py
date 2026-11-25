from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .models import User
from students.models import StudentProfile
from django.contrib import messages

def register_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        roll_no = request.POST.get('roll_no', '').strip().upper()
        password = request.POST.get('password', '')
        role = request.POST.get('role', '').strip()

        if not full_name or not roll_no or not password or role not in {'student', 'teacher'}:
            messages.error(request, "Please complete every required field.")
            return redirect('register')

        try:
            validate_password(password)
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
            return redirect('register')

        # The built-in username column stores the roll/staff ID for authentication.
        if User.objects.filter(username__iexact=roll_no).exists():
            messages.error(request, "This roll or staff ID is already registered.")
            return redirect('register')

        if role == 'student' and StudentProfile.objects.filter(roll_no__iexact=roll_no).exists():
            messages.error(request, "This roll number is already assigned to a student.")
            return redirect('register')

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=roll_no,
                    first_name=full_name,
                    password=password,
                    role=role,
                    # Teacher requests cannot authenticate until an admin approves them.
                    is_active=role == 'student',
                    teacher_approved=False,
                )
                if role == 'student':
                    StudentProfile.objects.create(user=user, roll_no=roll_no)
        except IntegrityError:
            messages.error(request, "This roll or staff ID is already registered.")
            return redirect('register')
        except Exception:
            messages.error(request, "Something went wrong during registration. Please try again.")
            return redirect('register')

        if role == 'teacher':
            messages.success(request, "Teacher registration request sent. An administrator must approve it before you can sign in.")
        else:
            messages.success(request, f"Account created for {user.display_name}.")
        return redirect('login')

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no', '').strip().upper()
        password = request.POST.get('password', '')

        if not roll_no or not password:
            messages.error(request, "Please enter both your roll or staff ID and password.")
            return redirect('login')

        user = authenticate(request, username=roll_no, password=password)

        if user is not None:
            if user.role == 'teacher' and not user.teacher_approved:
                messages.info(request, "Your teacher registration is still waiting for administrator approval.")
                return redirect('login')
            login(request, user)
            messages.success(request, f"Welcome, {user.display_name}!")
            return redirect('dashboard')

        # Inactive teacher requests do not authenticate, so explain the real next step.
        pending_teacher = User.objects.filter(
            username__iexact=roll_no,
            role='teacher',
            teacher_approved=False,
        ).first()
        if pending_teacher:
            messages.info(request, "Your teacher registration is waiting for administrator approval.")
        else:
            messages.error(request, "Invalid roll/staff ID or password.")
        return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully 👋")
    return redirect('login')

def home(request):
    return render(request, 'landing_page.html')
