from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomLoginForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=255)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False)
    birth_date = forms.DateField(required=False, widget=forms.SelectDateWidget(years=range(1900, 2025)))
    gender = forms.CharField(max_length=10, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    role = forms.ChoiceField(choices=[('patient', 'Patient')], required=False)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone_number', 'birth_date', 'gender', 'address', 'role', 'password1', 'password2']