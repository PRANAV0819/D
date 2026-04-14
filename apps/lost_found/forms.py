from django import forms
from .models import Item, ClaimRequest

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['item_type', 'title', 'description', 'category', 'location', 'date', 'image']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ClaimForm(forms.ModelForm):
    class Meta:
        model = ClaimRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe why this item is yours...'}),
        }