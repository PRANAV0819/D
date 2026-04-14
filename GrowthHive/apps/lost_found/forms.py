"""
apps/lost_found/forms.py

Forms for creating/editing Item reports and submitting ClaimRequests.
"""

from django import forms
from .models import Item, ClaimRequest


class ItemForm(forms.ModelForm):
    """Form for posting a Lost or Found item."""

    class Meta:
        model = Item
        fields = ["item_type", "title", "description", "category", "location", "date", "image"]
        widgets = {
            "item_type": forms.Select(attrs={"class": "form-control", "id": "id_item_type"}),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Blue water bottle", "id": "id_title"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Any identifying marks, brand, colour…",
                    "id": "id_description",
                }
            ),
            "category": forms.Select(attrs={"class": "form-control", "id": "id_category"}),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Library 2nd floor, Canteen",
                    "id": "id_location",
                }
            ),
            "date": forms.DateInput(
                attrs={"class": "form-control", "type": "date", "id": "id_date"}
            ),
            "image": forms.ClearableFileInput(
                attrs={"class": "form-control-file", "id": "id_image"}
            ),
        }
        labels = {
            "item_type": "Is this a Lost or Found report?",
            "title": "Item Title",
            "description": "Description (optional)",
            "category": "Category",
            "location": "Location",
            "date": "Date Lost / Found",
            "image": "Upload Photo (optional)",
        }


class ClaimForm(forms.ModelForm):
    """Form for submitting a claim on an item."""

    class Meta:
        model = ClaimRequest
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Explain why this item is yours — serial number, description, etc.",
                    "id": "id_claim_message",
                }
            )
        }
        labels = {"message": "Your Message to the Owner"}
