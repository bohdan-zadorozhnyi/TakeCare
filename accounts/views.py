from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

# Login view
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
    return render(request, 'accounts/login.html')

# Registration view
def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

# Home page view
def home_view(request):
    return render(request, 'home.html')

# Dashboard view (basic example, you can later customize per role)
@login_required
def dashboard_view(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    elif hasattr(request.user, 'doctorprofile'):
        return redirect('doctor_dashboard')
    elif hasattr(request.user, 'patientprofile'):
        return redirect('patient_dashboard')
    return render(request, 'dashboard.html')