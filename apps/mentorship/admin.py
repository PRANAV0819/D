from django.contrib import admin
from .models import MentorProfile, MentorshipRequest, MentorSession

admin.site.register(MentorProfile)
admin.site.register(MentorshipRequest)
admin.site.register(MentorSession)