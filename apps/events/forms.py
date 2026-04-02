from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model  = Event
        fields = ['title', 'event_type', 'description', 'banner', 'location', 'starts_at', 'ends_at', 'registration_link', 'max_participants', 'is_online']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'starts_at':   forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ends_at':     forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }