from django.core.mail import send_mail
from django.conf import settings
from .models import OTPVerification


def send_otp_email(user):
    """
    Generate a fresh OTP, email it, and return the OTPVerification object.
    In development the OTP prints to the terminal (console backend).
    """
    otp_obj  = OTPVerification.generate_for(user)
    expiry   = getattr(settings, 'OTP_EXPIRY_MINUTES', 10)

    subject = 'Your GrowthHive verification code'
    message = (
        f'Hi {user.first_name},\n\n'
        f'Your GrowthHive OTP is:\n\n'
        f'        {otp_obj.otp}\n\n'
        f'This code expires in {expiry} minutes.\n'
        f'If you did not sign up, please ignore this email.\n\n'
        f'— The GrowthHive Team'
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return otp_obj