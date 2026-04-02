from django import forms
from .models import Project, ProjectTask


class ProjectForm(forms.ModelForm):
    class Meta:
        model  = Project
        fields = ['title', 'description', 'skills_needed', 'max_members', 'github_url']
        widgets = {
            'description':   forms.Textarea(attrs={'rows': 4}),
            'skills_needed': forms.TextInput(attrs={'placeholder': 'e.g. React, Django, Figma'}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model  = ProjectTask
        fields = ['title', 'assigned_to', 'priority', 'status', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            approved_members = project.project_members.filter(is_approved=True).values_list('user', flat=True)
            from apps.accounts.models import User
            self.fields['assigned_to'].queryset = User.objects.filter(pk__in=approved_members)