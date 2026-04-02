from django import forms
from .models import Scholarship

class ScholarshipForm(forms.ModelForm):
    class Meta:
        model  = Scholarship
        fields = ['title', 'provider', 'amount', 'scholarship_type', 'description', 'eligibility', 'apply_link', 'deadline']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'eligibility': forms.Textarea(attrs={'rows': 3}),
            'deadline':    forms.DateInput(attrs={'type': 'date'}),
        }