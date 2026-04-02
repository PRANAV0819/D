from django.contrib import admin
from .models import Badge, UserBadge, UserActivity

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_required', 'icon']

admin.site.register(UserBadge)
admin.site.register(UserActivity)