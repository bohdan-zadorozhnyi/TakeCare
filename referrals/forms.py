from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Referral, ReferralDetails
from accounts.models import User

class ReferralForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(role='PATIENT'),
        widget=forms.Select(attrs={
            'class': 'form-control bg-white shadow-sm',
            'style': 'width: 100%; height: 38px; padding: 6px 12px;',
            'data-placeholder': 'Search for a patient...'
        }),
        label='Patient',
        required=True
    )

    expiration_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control bg-white shadow-sm',
            'style': 'width: 100%; height: 38px; padding: 6px 12px; resize: none;'
        })
    )
    
    class Meta:
        model = Referral
        fields = ['patient', 'specialist_type', 'expiration_date', 'notes']
        widgets = {
            'specialist_type': forms.Select(attrs={
                'class': 'form-control bg-white shadow-sm',
                'style': 'width: 100%; height: 38px; padding: 6px 12px;'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control bg-white shadow-sm',
                'rows': 4,
                'placeholder': 'Enter referral notes ...',
                'style': 'width: 100%; resize: vertical; padding: 6px 12px;'
            })
        }

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data.get('expiration_date')
        if expiration_date and expiration_date < timezone.now().date():
            raise forms.ValidationError("Expiration date cannot be in the past")
        return expiration_date

class ReferralDetailsForm(forms.ModelForm):
    class Meta:
        model = ReferralDetails
        fields = ['diagnosis', 'priority', 'additional_info']
        widgets = {
            'diagnosis': forms.TextInput(attrs={
                'class': 'form-control bg-white shadow-sm',
                'placeholder': 'Enter diagnosis (required)...',
                'style': 'width: 100%; height: 38px; padding: 6px 12px;'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control bg-white shadow-sm',
                'style': 'width: 100%; height: 38px; padding: 6px 12px;'
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'form-control bg-white shadow-sm',
                'rows': 3,
                'placeholder': 'Enter additional information...',
                'style': 'width: 100%; resize: vertical; padding: 6px 12px;'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        diagnosis = cleaned_data.get('diagnosis')
        
        if not diagnosis:
            raise forms.ValidationError({
                'diagnosis': 'Please specify the diagnosis for this referral'
            })
        return cleaned_data

class BaseReferralDetailsFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        has_valid_details = False
        
        for form in self.forms:
            if not form.is_valid():
                continue
                
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                diagnosis = form.cleaned_data.get('diagnosis')
                
                if diagnosis:
                    has_valid_details = True
        
        if not has_valid_details:
            raise forms.ValidationError(
                "Please provide at least one valid diagnosis for the referral."
            )

ReferralDetailsFormSet = inlineformset_factory(
    Referral, 
    ReferralDetails,
    form=ReferralDetailsForm,
    formset=BaseReferralDetailsFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)