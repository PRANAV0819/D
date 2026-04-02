from django.contrib import admin
from .models import Job, JobApplication

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display  = ['title', 'company', 'job_type', 'work_mode', 'status', 'posted_by', 'created_at']
    list_filter   = ['job_type', 'work_mode', 'status']
    search_fields = ['title', 'company']

@admin.register(JobApplication)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job', 'status', 'applied_at']
    list_filter  = ['status']