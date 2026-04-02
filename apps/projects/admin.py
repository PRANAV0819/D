from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Project, ProjectMember, ProjectTask

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'status', 'member_count', 'created_at']
    list_filter  = ['status']

admin.site.register(ProjectMember)
admin.site.register(ProjectTask)