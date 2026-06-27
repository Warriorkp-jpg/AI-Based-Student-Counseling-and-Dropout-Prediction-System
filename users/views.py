from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate,logout
from .models import User
from django.contrib import messages

def register_view(request):
    if request.method == 'POST':
       
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', '').strip()

      
        if not username or not password or not role:
            messages.error(request, "All fields are required! ⚠️")
            return redirect('register')

       
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long! 🔒")
            return redirect('register')

       
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists ❌")
            return redirect('register')

        try:
           
            user = User.objects.create_user(
                username=username,
                password=password,
                role=role
            )
            messages.success(request, f"Account created for {username}! ✅")
            return redirect('login')
        except Exception as e:
            messages.error(request, "Something went wrong during registration. Please try again.")
            return redirect('register')

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Please enter both username and password! ⚠️")
            return redirect('login')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome ,{user.username}! 🎉")
            return redirect('dashboard')
        else:
           
            messages.error(request, "Invalid username or password ❌")
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully 👋")
    return redirect('login')

def home(request):
    return render(request, 'landing_page.html')