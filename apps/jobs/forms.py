from django import forms
from .models import Job, JobApplication


class JobForm(forms.ModelForm):
    class Meta:
        model  = Job
        fields = ['title', 'company', 'location', 'job_type', 'work_mode',
                  'description', 'requirements', 'salary', 'deadline', 'apply_link']
        widgets = {
            'description':  forms.Textarea(attrs={'rows': 5}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
            'deadline':     forms.DateInput(attrs={'type': 'date'}),
        }


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model  = JobApplication
        fields = ['cover_note', 'resume']
        widgets = {
            'cover_note': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell the poster why you are a great fit…'
            }),
        }