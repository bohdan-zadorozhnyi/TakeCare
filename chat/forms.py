from django import forms
from .models import ChatRoom
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatRoomForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ChatRoom
        fields = ['name', 'participants']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }