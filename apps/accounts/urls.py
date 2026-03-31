from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth
    path('signup/',         views.signup_view,    name='signup'),
    path('login/',          views.login_view,     name='login'),
    path('logout/',         views.logout_view,    name='logout'),

    # OTP
    path('verify/',         views.verify_otp_view, name='verify_otp'),
    path('resend-otp/',     views.resend_otp_view, name='resend_otp'),

    # AJAX helper
    path('ajax/departments/', views.load_departments, name='load_departments'),

    # Dashboard
    path('dashboard/',      views.dashboard_view,  name='dashboard'),

    # Profile
    path('profile/',            views.profile_view,      name='profile'),
    path('profile/<int:user_id>/', views.profile_view,   name='profile_detail'),
    path('profile/edit/',       views.edit_profile_view, name='edit_profile'),

    # Skills
    path('skills/add/',            views.add_skill_view,    name='add_skill'),
    path('skills/remove/<int:skill_id>/', views.remove_skill_view, name='remove_skill'),
]