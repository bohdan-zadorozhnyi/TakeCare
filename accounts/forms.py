from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomLoginForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=255)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

class SignUpForm(UserCreationForm):
    """ Custom sign-up form for the User model """

    email = forms.EmailField(label='Email Address', max_length=75)
    name = forms.CharField(label='Full Name', max_length=255)
    phone_number = forms.CharField(label='Phone Number', max_length=15)
    personal_id = forms.CharField(label='Personal ID', max_length=50)
    birth_date = forms.DateField(
        label='Birth Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'birthdate-picker'})
    )
    gender = forms.ChoiceField(label='Gender', choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')])
    address = forms.CharField(label='Address',  max_length=255)

    class Meta:
        model = User
        fields = ('email', 'name', 'phone_number', 'address', 'birth_date', 'gender', 'password1', 'password2', 'personal_id')

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            user = User.objects.get(email=email)
            raise forms.ValidationError("This email address already exists. Did you forget your password?")
        except User.DoesNotExist:
            return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data["email"]
        user.role = 'PATIENT'
        user.is_active = True  # Set this to False if you use email verification
        user.name = self.cleaned_data["name"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.personal_id = self.cleaned_data["personal_id"]
        user.birth_date = self.cleaned_data["birth_date"]
        user.gender = self.cleaned_data["gender"]
        user.address = self.cleaned_data["address"]
        #user.role = self.cleaned_data["role"]

        if commit:
            user.save()
        return user