"""
apps/users/admin.py

Production admin setup:
- UserAdmin extends the default Django UserAdmin with our custom fields
- ProfileInline renders the profile inside the user admin page
  (no need to navigate to two pages to see the full picture)
- ActivityStats and ActivityEvent are read-only in admin — they're
  written by signals, not by hand
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import ActivityEvent, ActivityStats, Profile, User


# ---------------------------------------------------------------------------
# Profile inline — shown inside the User change page
# ---------------------------------------------------------------------------


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"
    fields = (
        "bio",
        "department",
        "year",
        "skills",
        "github_link",
        "linkedin_link",
        "website_link",
        "is_public",
        "avatar",
    )


class ActivityStatsInline(admin.TabularInline):
    model = ActivityStats
    can_delete = False
    verbose_name_plural = "Activity stats"
    readonly_fields = (
        "mentorship_requests_sent",
        "mentorship_requests_received",
        "mentorships_completed",
        "projects_created",
        "projects_joined",
        "resources_uploaded",
        "opportunities_applied",
        "login_count",
        "last_active_at",
        "total_contributions_display",
    )

    # Prevent any field from being editable in admin
    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Total contributions")
    def total_contributions_display(self, obj):
        return obj.total_contributions if obj else "—"


# ---------------------------------------------------------------------------
# User admin
# ---------------------------------------------------------------------------


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, ActivityStatsInline)
    list_display = (
        "email",
        "get_full_name",
        "role",
        "is_active",
        "is_deleted",
        "created_at",
    )
    list_filter = ("role", "is_active", "is_deleted", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)
    list_per_page = 50

    # Fieldsets — redefine to add role field and remove username prominence
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name")},
        ),
        (
            _("Role & status"),
            {"fields": ("role", "is_active", "is_deleted", "is_staff", "is_superuser")},
        ),
        (
            _("Permissions"),
            {
                "classes": ("collapse",),
                "fields": ("groups", "user_permissions"),
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ("collapse",),
                "fields": ("last_login", "created_at", "updated_at"),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "password1", "password2"),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "last_login")


# ---------------------------------------------------------------------------
# Profile admin — for direct browsing
# ---------------------------------------------------------------------------


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "year", "is_public", "updated_at")
    list_filter = ("department", "year", "is_public")
    search_fields = ("user__email", "bio")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user",)


# ---------------------------------------------------------------------------
# Activity admin — read-only audit views
# ---------------------------------------------------------------------------


@admin.register(ActivityStats)
class ActivityStatsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "total_contributions_display",
        "mentorship_requests_sent",
        "projects_joined",
        "resources_uploaded",
        "last_active_at",
    )
    search_fields = ("user__email",)
    readonly_fields = [f.name for f in ActivityStats._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Contributions")
    def total_contributions_display(self, obj):
        return obj.total_contributions


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ("user", "event_type", "label", "event_date", "created_at")
    list_filter = ("event_type", "event_date")
    search_fields = ("user__email", "label")
    date_hierarchy = "event_date"
    readonly_fields = [f.name for f in ActivityEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
