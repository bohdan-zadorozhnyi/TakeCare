from django import forms
from .models import Article

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }