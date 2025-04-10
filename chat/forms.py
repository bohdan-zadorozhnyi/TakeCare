from django import forms
from .models import ChatRoom
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class ChatRoomForm(forms.ModelForm):
    participant = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select User to Chat With'
    )

    class Meta:
        model = ChatRoom
        fields = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['participant'].queryset = User.objects.exclude(id=user.id)
            self.fields['participant'].label_from_instance = lambda obj: obj.name or f"User {obj.id}"
            
    def save(self, user=None, commit=True):
        instance = super().save(commit=False)
        other_user = self.cleaned_data['participant']
        instance.name = other_user.name or f"User {other_user.id}"
        
        # Save the instance first
        if commit and user:
            instance.save()
            # Then add participants
            instance.participants.add(user, other_user)
        
        return instance