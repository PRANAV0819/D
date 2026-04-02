from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Scholarship

@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ['title', 'provider', 'scholarship_type', 'deadline', 'is_active']
    list_filter  = ['scholarship_type', 'is_active']