from django import forms
from .models import LostFoundItem

class LostFoundForm(forms.ModelForm):
    class Meta:
        model  = LostFoundItem
        fields = ['item_type', 'title', 'description', 'location', 'deposited_at', 'image']
        widgets = {
            'title':        forms.TextInput(attrs={'placeholder': 'e.g. Black Umbrella'}),
            'description':  forms.Textarea(attrs={'rows': 3}),
            'location':     forms.TextInput(attrs={'placeholder': 'e.g. Library 2nd floor'}),
            'deposited_at': forms.TextInput(attrs={'placeholder': 'e.g. Security Desk, Block A'}),
        }