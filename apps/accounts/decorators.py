from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def verified_required(func):
    """Block unverified users from accessing a view."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_email_verified:
            messages.warning(request, 'Please verify your email to continue.')
            return redirect('accounts:verify_otp')
        return func(request, *args, **kwargs)
    return wrapper


def student_required(func):
    """Restrict a view to students only."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_student:
            messages.error(request, 'This feature is for students only.')
            return redirect('accounts:dashboard')
        return func(request, *args, **kwargs)
    return wrapper


def alumni_or_teacher_required(func):
    """Restrict a view to alumni and teachers."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.is_student:
            messages.error(request, 'This feature is for alumni and teachers only.')
            return redirect('accounts:dashboard')
        return func(request, *args, **kwargs)
    return wrapper