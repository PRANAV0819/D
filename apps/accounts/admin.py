from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, College, Department, Skill, UserSkill, OTPVerification
# Note: College model kept for admin management; college FK removed from User


# ─────────────────────────────────────────────
# College
# ─────────────────────────────────────────────

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'domain', 'city', 'state']
    search_fields = ['name', 'domain']


# ─────────────────────────────────────────────
# Department
# ─────────────────────────────────────────────

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'college']
    list_filter   = ['college']
    search_fields = ['name', 'code']


# ─────────────────────────────────────────────
# Profile Inline (inside User)
# ─────────────────────────────────────────────

class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0


# ─────────────────────────────────────────────
# User Admin
# ─────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines       = [ProfileInline]
    list_display  = ['email', 'get_full_name', 'role', 'is_email_verified', 'is_active']
    list_filter   = ['role', 'is_email_verified']
    search_fields = ['email', 'first_name', 'last_name']
    ordering      = ['-created_at']

    fieldsets = (
        (None,           {'fields': ('email', 'password')}),
        ('Personal',     {'fields': ('first_name', 'last_name', 'role', 'department')}),
        ('Verification', {'fields': ('is_email_verified',)}),
        ('Permissions',  {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


# ─────────────────────────────────────────────
# Skill
# ─────────────────────────────────────────────

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


# ─────────────────────────────────────────────
# ✅ FIXED UserSkill Admin
# ─────────────────────────────────────────────

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display  = ['get_user', 'skill', 'level']
    list_filter   = ['level']
    search_fields = ['profile__user__email', 'skill__name']

    def get_user(self, obj):
        return obj.profile.user.get_full_name()

    get_user.short_description = 'User'


# ─────────────────────────────────────────────
# OTP Verification
# ─────────────────────────────────────────────

@admin.register(OTPVerification)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp', 'is_used', 'created_at']
    list_filter  = ['is_used']