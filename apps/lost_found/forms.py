from django import forms
from .models import LostFoundItem

class LostFoundForm(forms.ModelForm):
    class Meta:
        model  = LostFoundItem
        fields = ['item_type', 'title', 'description', 'location', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'location':    forms.TextInput(attrs={'placeholder': 'e.g. Library 2nd floor'}),
        }