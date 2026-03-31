"""
apps/users/forms.py

Why forms in a DRF-first project?
  The profile edit page is rendered server-side (Django templates) for
  the MVP. DRF serializers handle the API surface separately.
  Forms handle validation, widget customization, and CSRF protection.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator

from .models import Profile

User = get_user_model()


# ---------------------------------------------------------------------------
# User basic info form (name fields on User model)
# ---------------------------------------------------------------------------


class UserBasicForm(forms.ModelForm):
    """Edits first_name and last_name on the User model."""

    class Meta:
        model = User
        fields = ("first_name", "last_name")
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "First name",
                    "maxlength": "150",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Last name",
                    "maxlength": "150",
                }
            ),
        }


# ---------------------------------------------------------------------------
# Profile edit form
# ---------------------------------------------------------------------------


class ProfileEditForm(forms.ModelForm):
    """
    Full profile edit form.

    skills_raw: a hidden CharField that receives a comma-separated string
    from a JavaScript tag-input widget. clean_skills_raw() converts it
    to the list expected by the ArrayField.
    """

    # Rendered as a comma-separated string; JS tag widget populates it
    skills_raw = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "skills-raw-input"}),
        help_text="Managed by the tag widget — do not edit manually.",
    )

    class Meta:
        model = Profile
        fields = (
            "bio",
            "department",
            "year",
            "avatar",
            "github_link",
            "linkedin_link",
            "website_link",
            "is_public",
        )
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "class": "form-input form-textarea",
                    "rows": 4,
                    "placeholder": "Tell the community about yourself…",
                    "maxlength": "500",
                }
            ),
            "department": forms.Select(attrs={"class": "form-select"}),
            "year": forms.Select(attrs={"class": "form-select"}),
            "avatar": forms.ClearableFileInput(
                attrs={
                    "class": "form-file-input",
                    "accept": "image/*",
                }
            ),
            "github_link": forms.URLInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "https://github.com/yourusername",
                }
            ),
            "linkedin_link": forms.URLInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "https://linkedin.com/in/yourusername",
                }
            ),
            "website_link": forms.URLInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "https://yourwebsite.com",
                }
            ),
            "is_public": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }
        labels = {
            "is_public": "Make my profile public",
        }

    def clean_skills_raw(self) -> list[str]:
        """Convert 'Python, Django, React' → ['Python', 'Django', 'React']."""
        raw = self.cleaned_data.get("skills_raw", "")
        skills = [s.strip().title() for s in raw.split(",") if s.strip()]
        # Deduplicate while preserving order
        seen, unique = set(), []
        for s in skills:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique

    def clean_github_link(self) -> str:
        url = self.cleaned_data.get("github_link", "")
        if url and "github.com" not in url:
            raise forms.ValidationError("Please enter a valid GitHub profile URL.")
        return url

    def clean_linkedin_link(self) -> str:
        url = self.cleaned_data.get("linkedin_link", "")
        if url and "linkedin.com" not in url:
            raise forms.ValidationError("Please enter a valid LinkedIn profile URL.")
        return url

    def save(self, commit: bool = True) -> Profile:
        profile = super().save(commit=False)
        # Write the parsed skill list from the hidden field
        skills = self.cleaned_data.get("skills_raw")
        if skills is not None:  # empty list is a valid write (clears skills)
            profile.skills = skills
        if commit:
            profile.save()
        return profile
