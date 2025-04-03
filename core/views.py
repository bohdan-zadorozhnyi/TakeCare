from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.shortcuts import render

@login_required
def home_view(request):
    return render(request, 'home.html')

def about_view(request):
    return render(request, 'about.html')