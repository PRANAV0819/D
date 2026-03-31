"""
apps/users/serializers.py

DRF serializers — used by the REST API layer.
These sit alongside but separate from the Django forms (forms.py).
Forms = server-side rendered HTML; Serializers = JSON API.

Serializers follow a read / write split:
  *ReadSerializer   — used for GET responses (rich, nested)
  *WriteSerializer  — used for PATCH / POST (flat, validated input)

This prevents over-posting and gives clean Swagger documentation.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ActivityStats, Profile

User = get_user_model()


# ---------------------------------------------------------------------------
# Activity stats — read-only nested object
# ---------------------------------------------------------------------------


class ActivityStatsSerializer(serializers.ModelSerializer):
    total_contributions = serializers.IntegerField(read_only=True)

    class Meta:
        model = ActivityStats
        fields = (
            "mentorship_requests_sent",
            "mentorship_requests_received",
            "mentorships_completed",
            "projects_created",
            "projects_joined",
            "resources_uploaded",
            "opportunities_applied",
            "login_count",
            "last_active_at",
            "total_contributions",
        )
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Profile — read vs write split
# ---------------------------------------------------------------------------


class ProfileReadSerializer(serializers.ModelSerializer):
    avatar_url = serializers.CharField(read_only=True)
    department_display = serializers.CharField(
        source="get_department_display", read_only=True
    )
    year_display = serializers.CharField(source="get_year_display", read_only=True)

    class Meta:
        model = Profile
        fields = (
            "bio",
            "skills",
            "department",
            "department_display",
            "year",
            "year_display",
            "avatar_url",
            "github_link",
            "linkedin_link",
            "website_link",
            "is_public",
        )


class ProfileWriteSerializer(serializers.ModelSerializer):
    """Accepts a list of strings for skills (validated by DRF)."""

    skills = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        max_length=20,
    )

    class Meta:
        model = Profile
        fields = (
            "bio",
            "skills",
            "department",
            "year",
            "avatar",
            "github_link",
            "linkedin_link",
            "website_link",
            "is_public",
        )

    def validate_github_link(self, value: str) -> str:
        if value and "github.com" not in value:
            raise serializers.ValidationError("Must be a valid GitHub URL.")
        return value

    def validate_linkedin_link(self, value: str) -> str:
        if value and "linkedin.com" not in value:
            raise serializers.ValidationError("Must be a valid LinkedIn URL.")
        return value

    def validate_skills(self, value: list[str]) -> list[str]:
        return [s.strip().title() for s in value if s.strip()]


# ---------------------------------------------------------------------------
# User — public profile view
# ---------------------------------------------------------------------------


class UserPublicSerializer(serializers.ModelSerializer):
    """Read-only representation shown to other users."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    profile = ProfileReadSerializer(read_only=True)
    activity = ActivityStatsSerializer(read_only=True)
    is_mentor_eligible = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "email",
            "role",
            "role_display",
            "is_mentor_eligible",
            "profile",
            "activity",
            "created_at",
        )
        read_only_fields = fields


class UserSelfSerializer(serializers.ModelSerializer):
    """
    Serializer for the authenticated user editing their own account.
    PATCH /api/v1/users/me/
    """

    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    profile = ProfileWriteSerializer(required=False)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "profile")

    def update(self, instance: User, validated_data: dict) -> User:
        profile_data = validated_data.pop("profile", None)

        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=list(validated_data.keys()) + ["updated_at"])

        # Update Profile fields (nested write)
        if profile_data:
            profile_serializer = ProfileWriteSerializer(
                instance.profile,
                data=profile_data,
                partial=True,
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        return instance
