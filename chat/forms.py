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
        fields = []  # name will be set automatically

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['participant'].queryset = User.objects.exclude(id=user.id)
            # Override the label_from_instance to show name
            self.fields['participant'].label_from_instance = lambda obj: obj.name or f"User {obj.id}"
            
    def save(self, user=None, commit=True):
        instance = super().save(commit=False)
        if commit and user:
            instance.save()
            other_user = self.cleaned_data['participant']
            instance.name = other_user.name or f"User {other_user.id}"
            instance.participants.add(user, other_user)
            instance.save()
        return instance