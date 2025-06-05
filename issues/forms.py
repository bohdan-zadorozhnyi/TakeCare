from django import forms
from .models import Issue

class IssueReportForm(forms.ModelForm):
    """
    Form for users to report issues
    """
    class Meta:
        model = Issue
        fields = ['title', 'message']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description of the issue'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Please describe the issue in detail'}),
        }
        
class AdminIssueResponseForm(forms.ModelForm):
    """
    Form for admins to respond to issues
    """
    class Meta:
        model = Issue
        fields = ['status', 'admin_notes', 'admin_response']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes (not visible to users)'}),
            'admin_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Response to the user'}),
        }
