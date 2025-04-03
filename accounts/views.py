from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import CustomLoginForm, SignUpForm
from TakeCare.backends import EmailAuthBackend

# Login view
def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            backend = EmailAuthBackend()
            user = backend.authenticate(request=request, username=email, password=password)
            print(f"DEBUG: Found user - {user}")
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Email or Password is incorrect.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')
# Registration view
def register_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'accounts/register.html', {'form': form})
