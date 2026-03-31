"""
apps/core/permissions.py

Reusable DRF permission classes used across all GrowthHive apps.
Import and apply at the view level:

    from apps.core.permissions import IsStudent, IsMentorEligible

    class MentorshipRequestView(APIView):
        permission_classes = [IsAuthenticated, IsStudent]
"""

from rest_framework.permissions import BasePermission, IsAuthenticated


class IsStudent(BasePermission):
    message = "Only students can perform this action."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user and request.user.is_authenticated and request.user.is_student
        )


class IsAlumni(BasePermission):
    message = "Only alumni can perform this action."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user and request.user.is_authenticated and request.user.is_alumni
        )


class IsMentorEligible(BasePermission):
    """Alumni and seniors can act as mentors."""

    message = "Only alumni or seniors can perform this action."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_mentor_eligible
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission.
    The object must have a `user` attribute (Profile, ActivityStats, etc.)
    or be a User instance directly.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_staff:
            return True
        target_user = getattr(obj, "user", obj)
        return target_user == request.user


class IsProfilePublicOrOwner(BasePermission):
    """Read-only check: allow if profile is public, or the owner is requesting."""

    message = "This profile is private."

    def has_object_permission(self, request, view, obj) -> bool:
        profile = getattr(obj, "profile", obj)
        if request.user.is_staff:
            return True
        if profile.is_public:
            return True
        return request.user.is_authenticated and profile.user == request.user
