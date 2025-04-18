from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Prescription, PrescriptionMedication
from accounts.models import User

class PrescriptionForm(forms.ModelForm):
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
        model = Prescription
        fields = ['patient', 'expiration_date', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control bg-white shadow-sm',
                'rows': 4,
                'placeholder': 'Enter prescription notes (required)...',
                'style': 'width: 100%; resize: vertical; padding: 6px 12px;'
            })
        }

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data.get('expiration_date')
        if expiration_date and expiration_date < timezone.now().date():
            raise forms.ValidationError("Expiration date cannot be in the past")
        return expiration_date

class PrescriptionMedicationForm(forms.ModelForm):
    class Meta:
        model = PrescriptionMedication
        fields = ['medication_name', 'dosage']
        widgets = {
            'medication_name': forms.TextInput(attrs={
                'class': 'form-control bg-white shadow-sm',
                'placeholder': 'Enter medication name (required)...',
                'style': 'width: 100%; height: 38px; padding: 6px 12px;'
            }),
            'dosage': forms.TextInput(attrs={
                'class': 'form-control bg-white shadow-sm',
                'placeholder': 'Enter dosage details (required)...',
                'style': 'width: 100%; height: 38px; padding: 6px 12px;'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        medication_name = cleaned_data.get('medication_name')
        dosage = cleaned_data.get('dosage')

        if medication_name and not dosage:
            raise forms.ValidationError({
                'dosage': 'Please specify the dosage for this medication'
            })
        elif dosage and not medication_name:
            raise forms.ValidationError({
                'medication_name': 'Please specify the name of the medication'
            })
        return cleaned_data

class BasePrescriptionMedicationFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        has_valid_medication = False
        incomplete_medications = []
        
        for i, form in enumerate(self.forms, 1):
            if not form.is_valid():
                continue
                
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                medication_name = form.cleaned_data.get('medication_name')
                dosage = form.cleaned_data.get('dosage')
                
                if medication_name and dosage:
                    has_valid_medication = True
                elif medication_name or dosage:
                    incomplete_medications.append(f"Medication {i}")
        
        if not has_valid_medication:
            if incomplete_medications:
                raise forms.ValidationError(
                    f"Incomplete medication details for: {', '.join(incomplete_medications)}. "
                    "Please provide both name and dosage."
                )
            else:
                raise forms.ValidationError(
                    "Please provide at least one medication with both name and dosage."
                )

PrescriptionMedicationFormSet = inlineformset_factory(
    Prescription, 
    PrescriptionMedication,
    form=PrescriptionMedicationForm,
    formset=BasePrescriptionMedicationFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)