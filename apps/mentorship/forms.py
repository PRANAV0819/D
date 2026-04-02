from django import forms
from .models import MentorProfile, MentorshipRequest, MentorSession


class MentorProfileForm(forms.ModelForm):
    class Meta:
        model  = MentorProfile
        fields = ['expertise', 'experience', 'bio', 'is_active']
        widgets = {
            'expertise': forms.TextInput(attrs={'placeholder': 'e.g. Python, Career, DSA, UI/UX'}),
            'bio':       forms.Textarea(attrs={'rows': 3}),
        }


class MentorshipRequestForm(forms.ModelForm):
    class Meta:
        model  = MentorshipRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Explain what you want help with and your goals…'
            })
        }


class MentorSessionForm(forms.ModelForm):
    class Meta:
        model  = MentorSession
        fields = ['title', 'scheduled_at', 'duration_min', 'meeting_link', 'notes']
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes':        forms.Textarea(attrs={'rows': 3}),
        }