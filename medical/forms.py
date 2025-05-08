from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory, BaseInlineFormSet
from zope.interface.common import optional

from .models import MedicalRecord
from accounts.models import User

class MedicalRecordForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(role='PATIENT'),
        widget=forms.Select(attrs={
            'class': 'form-control bg-white shadow-sm',
            'style': 'width: 100%; height: 38px; padding: 6px 12px;',
            'data-placeholder': 'Search for a patient...'
        }),
        label='Patient',
        required=True)

    class Meta:
        model = MedicalRecord
        fields = ['patient', 'condition', 'treatment', 'notes', 'file']
        widgets = {
            'condition': forms.Textarea(attrs={'rows': 3}),
            'treatment': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(MedicalRecordForm, self).__init__(*args, **kwargs)
        self.fields['file'].required = False


class EditMedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['condition', 'treatment', 'notes', 'file']
        widgets = {
            'condition': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'treatment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(EditMedicalRecordForm, self).__init__(*args, **kwargs)
        self.fields['file'].required = False
