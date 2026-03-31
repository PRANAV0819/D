"""
apps/users/views.py

View architecture:
  ProfileView     — public-facing profile page (own or others')
  EditProfileView — combined User + Profile form edit (login required)
  ActivityHeatmapView — AJAX endpoint returning heatmap data as JSON

All views are class-based and inherit from Django's built-in mixins.
Login-required views use LoginRequiredMixin so the redirect happens
at the mixin level — not scattered across view logic.

select_related / prefetch_related are used on every queryset that
touches User → Profile → ActivityStats to avoid N+1 queries.
"""

import json
from collections import defaultdict
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, UpdateView, View
from django.urls import reverse_lazy, reverse

from .forms import ProfileEditForm, UserBasicForm
from .models import ActivityEvent, ActivityStats, Profile

User = get_user_model()


# ---------------------------------------------------------------------------
# Helper: fetch a fully-hydrated user object in one query
# ---------------------------------------------------------------------------


def get_full_user(pk):
    """
    Return a User with profile and activity pre-fetched.
    Raises Http404 if not found or soft-deleted.
    """
    return get_object_or_404(
        User.objects.select_related("profile", "activity").filter(
            is_deleted=False, is_active=True
        ),
        pk=pk,
    )


# ---------------------------------------------------------------------------
# Profile view — public profile page
# ---------------------------------------------------------------------------


class ProfileView(TemplateView):
    """
    Renders /users/<pk>/profile/

    Visibility rules:
      - If the profile is private: only the owner and admins can see it.
      - Everyone else gets a 404 (not a 403, to avoid user enumeration).
    """

    template_name = "users/profile.html"

    def get(self, request, pk, *args, **kwargs):
        target_user = get_full_user(pk)
        profile = target_user.profile

        is_owner = request.user.is_authenticated and request.user.pk == target_user.pk
        is_admin = request.user.is_authenticated and request.user.is_staff

        if not profile.is_public and not is_owner and not is_admin:
            raise Http404

        # Heatmap: last 52 weeks of activity (one year)
        since = date.today() - timedelta(weeks=52)
        events = (
            ActivityEvent.objects.filter(user=target_user, event_date__gte=since)
            .values("event_date", "event_type")
            .order_by("event_date")
        )

        # Build a dict: {date_str: count} for the heatmap JS widget
        heatmap_data: dict[str, int] = defaultdict(int)
        for ev in events:
            heatmap_data[ev["event_date"].isoformat()] += 1

        context = {
            "target_user": target_user,
            "profile": profile,
            "activity": getattr(target_user, "activity", None),
            "heatmap_json": json.dumps(dict(heatmap_data)),
            "is_owner": is_owner,
        }
        return self.render_to_response(context)


# ---------------------------------------------------------------------------
# Edit profile view — owner only
# ---------------------------------------------------------------------------


class EditProfileView(LoginRequiredMixin, TemplateView):
    """
    Renders and processes /users/profile/edit/

    Two forms rendered on the same page:
      UserBasicForm   → first_name, last_name on User
      ProfileEditForm → everything on Profile

    Saved in a single atomic transaction so partial saves don't happen.
    """

    template_name = "users/edit_profile.html"
    success_url = None  # set dynamically in post()

    def _get_forms(self, data=None, files=None):
        user = self.request.user
        profile = user.profile
        return (
            UserBasicForm(data, instance=user, prefix="user"),
            ProfileEditForm(data, files, instance=profile, prefix="profile"),
        )

    def get(self, request, *args, **kwargs):
        user_form, profile_form = self._get_forms()
        return self.render_to_response(self._build_context(user_form, profile_form))

    def post(self, request, *args, **kwargs):
        user_form, profile_form = self._get_forms(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    profile_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect(
                    reverse("users:profile", kwargs={"pk": request.user.pk})
                )
            except Exception:
                messages.error(request, "Something went wrong. Please try again.")

        return self.render_to_response(self._build_context(user_form, profile_form))

    def _build_context(self, user_form, profile_form) -> dict:
        profile = self.request.user.profile
        return {
            "user_form": user_form,
            "profile_form": profile_form,
            # Pass current skills as JSON for the tag widget to initialise
            "skills_json": json.dumps(profile.skills),
        }


# ---------------------------------------------------------------------------
# AJAX heatmap endpoint
# ---------------------------------------------------------------------------


class ActivityHeatmapView(LoginRequiredMixin, View):
    """
    GET /users/<pk>/heatmap/?weeks=52

    Returns JSON for the GitHub-style contribution heatmap.
    Only the profile owner can fetch their own heatmap data.
    """

    def get(self, request, pk, *args, **kwargs):
        if request.user.pk != pk and not request.user.is_staff:
            return JsonResponse({"error": "Forbidden"}, status=403)

        try:
            weeks = max(1, min(int(request.GET.get("weeks", 52)), 104))
        except ValueError:
            weeks = 52

        since = date.today() - timedelta(weeks=weeks)
        events = ActivityEvent.objects.filter(
            user_id=pk,
            event_date__gte=since,
        ).values("event_date", "event_type")

        data: dict[str, int] = defaultdict(int)
        for ev in events:
            data[ev["event_date"].isoformat()] += 1

        return JsonResponse({"heatmap": data, "weeks": weeks})
