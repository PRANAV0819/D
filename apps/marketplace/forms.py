from django import forms
from .models import MarketplaceItem

class MarketplaceItemForm(forms.ModelForm):
    class Meta:
        model  = MarketplaceItem
        fields = ['title', 'description', 'price', 'condition', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price':       forms.NumberInput(attrs={'placeholder': '499.00'}),
        }