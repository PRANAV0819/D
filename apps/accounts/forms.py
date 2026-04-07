from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Profile, Department, Skill, UserSkill, DEPARTMENT_CHOICES


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Create a password'}),
    )
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password'}),
    )

    class Meta:
        model  = User
        # College field intentionally removed from signup
        fields = ['first_name', 'last_name', 'email', 'role', 'department']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name':  forms.TextInput(attrs={'placeholder': 'Last name'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'Email address'}),
            'role':       forms.Select(),
            'department': forms.Select(choices=DEPARTMENT_CHOICES),
        }

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError({'password2': 'Passwords do not match.'})
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = True
        user.is_email_verified = False
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    def clean(self):
        cleaned = super().clean()
        email    = cleaned.get('email')
        password = cleaned.get('password')
        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise forms.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise forms.ValidationError('This account has been deactivated.')
            cleaned['user'] = user
        return cleaned


class OTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': '000000',
            'class': 'otp-input',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'maxlength': '6',
        }),
        label='Enter 6-digit OTP',
    )


class ProfileEditForm(forms.ModelForm):
    # User fields surfaced on the profile edit page
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name  = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    class Meta:
        model  = Profile
        fields = [
            'bio', 'avatar', 'banner',
            'graduation_year', 'current_year',
            'github_url', 'linkedin_url', 'website', 'location',
            'resume', 'is_open_to_work', 'is_open_to_mentor',
        ]
        widgets = {
            'bio':             forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a short bio...'}),
            'location':        forms.TextInput(attrs={'placeholder': 'City, Country'}),
            'github_url':      forms.URLInput(attrs={'placeholder': 'https://github.com/username'}),
            'linkedin_url':    forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/username'}),
            'website':         forms.URLInput(attrs={'placeholder': 'https://yourwebsite.com'}),
            'graduation_year': forms.NumberInput(attrs={'placeholder': '2026'}),
            'current_year':    forms.NumberInput(attrs={'placeholder': '3'}),
        }

    def __init__(self, *args, **kwargs):
        # Accept the user instance so we can pre-fill name fields
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial  = self.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name  = self.cleaned_data['last_name']
            self.user.save(update_fields=['first_name', 'last_name'])
        if commit:
            profile.save()
        return profile


class SkillForm(forms.ModelForm):
    skill_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Python, React, UI/UX'}),
        label='Skill',
    )

    class Meta:
        model  = UserSkill
        fields = ['level']

    def clean_skill_name(self):
        name  = self.cleaned_data['skill_name'].strip().title()
        skill, _ = Skill.objects.get_or_create(
            name__iexact=name,
            defaults={'name': name},
        )
        return skill