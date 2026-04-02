from django import forms
from .models import Resource

class ResourceForm(forms.ModelForm):
    class Meta:
        model  = Resource
        fields = ['title', 'description', 'category', 'department', 'subject', 'file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }