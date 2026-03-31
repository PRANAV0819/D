from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import User, Profile, OTPVerification, Department, UserSkill, Skill
from .forms import SignupForm, LoginForm, OTPForm, ProfileEditForm, SkillForm
from .utils import send_otp_email
from .decorators import verified_required


# ── Signup ────────────────────────────────────────────────────────────

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        send_otp_email(user)
        # Store user pk in session so verify_otp knows who to verify
        request.session['pending_verification_user_id'] = user.pk
        messages.success(
            request,
            f'Account created! Check your email ({user.email}) for the OTP.'
        )
        return redirect('accounts:verify_otp')

    return render(request, 'accounts/signup.html', {'form': form})


# ── Email OTP verification ────────────────────────────────────────────

def verify_otp_view(request):
    # Get the user waiting for verification
    user_id = request.session.get('pending_verification_user_id')
    if not user_id:
        # If the logged-in user hasn't verified yet
        if request.user.is_authenticated and not request.user.is_email_verified:
            user_id = request.user.pk
        else:
            return redirect('accounts:login')

    user = get_object_or_404(User, pk=user_id)

    form = OTPForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        entered = form.cleaned_data['otp']
        otp_obj = (
            OTPVerification.objects
            .filter(user=user, is_used=False)
            .order_by('-created_at')
            .first()
        )
        if otp_obj is None:
            messages.error(request, 'No active OTP found. Please request a new one.')
        elif otp_obj.is_expired():
            messages.error(request, 'OTP has expired. Please request a new one.')
        elif otp_obj.otp != entered:
            messages.error(request, 'Incorrect OTP. Please try again.')
        else:
            otp_obj.is_used = True
            otp_obj.save()
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            # Clear session key
            request.session.pop('pending_verification_user_id', None)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Email verified! Welcome to GrowthHive.')
            return redirect('accounts:dashboard')

    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'email': user.email,
    })


def resend_otp_view(request):
    user_id = request.session.get('pending_verification_user_id')
    if not user_id and request.user.is_authenticated:
        user_id = request.user.pk

    if user_id:
        user = get_object_or_404(User, pk=user_id)
        if not user.is_email_verified:
            send_otp_email(user)
            messages.success(request, 'A new OTP has been sent to your email.')
    return redirect('accounts:verify_otp')


# ── Login / Logout ────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.cleaned_data['user']

        if not user.is_email_verified:
            request.session['pending_verification_user_id'] = user.pk
            send_otp_email(user)
            messages.info(request, 'Please verify your email first. A new OTP has been sent.')
            return redirect('accounts:verify_otp')

        login(request, user)
        messages.success(request, f'Welcome back, {user.first_name}!')
        next_url = request.GET.get('next', 'accounts:dashboard')
        return redirect(next_url)

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


# ── AJAX: load departments for selected college ───────────────────────

def load_departments(request):
    from django.http import JsonResponse
    college_id = request.GET.get('college_id')
    departments = Department.objects.filter(college_id=college_id).values('id', 'name', 'code')
    return JsonResponse({'departments': list(departments)})


# ── Dashboard ─────────────────────────────────────────────────────────

@login_required
@verified_required
@login_required
def dashboard_view(request):
    # ✅ Get logged-in user's profile
    profile = request.user.profile

    # ✅ Correct way to get user skills (FIXED)
    user_skills = UserSkill.objects.filter(
        profile__user=request.user
    ).select_related('skill')

    context = {
        'profile': profile,
        'skills': user_skills,
    }

    return render(request, 'accounts/dashboard.html', context)

# ── Profile (public view) ─────────────────────────────────────────────

@login_required
@verified_required
def profile_view(request, user_id=None):
    if user_id:
        target_user = get_object_or_404(User, pk=user_id, is_active=True)
    else:
        target_user = request.user

    profile    = target_user.profile
    user_skills = UserSkill.objects.filter(user=target_user).select_related('skill')
    is_own     = (target_user == request.user)

    return render(request, 'accounts/profile.html', {
        'target_user': target_user,
        'profile':     profile,
        'user_skills': user_skills,
        'is_own':      is_own,
    })


# ── Edit Profile ──────────────────────────────────────────────────────

@login_required
@verified_required
def edit_profile_view(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileEditForm(
            request.POST, request.FILES,
            instance=profile,
            user=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form, 'profile': profile})


# ── Add skill ─────────────────────────────────────────────────────────

@login_required
@verified_required
def add_skill_view(request):
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.cleaned_data['skill_name']
            level = form.cleaned_data['level']
            UserSkill.objects.update_or_create(
                user=request.user, skill=skill,
                defaults={'level': level},
            )
            messages.success(request, f'Skill "{skill.name}" added.')
    return redirect('accounts:edit_profile')


@login_required
@require_POST
def remove_skill_view(request, skill_id):
    UserSkill.objects.filter(user=request.user, skill_id=skill_id).delete()
    messages.success(request, 'Skill removed.')
    return redirect('accounts:edit_profile')