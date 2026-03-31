"""
apps/users/urls.py

Namespace: "users"
Mount in root urls.py as:
    path("users/", include("apps.users.urls", namespace="users")),
"""

from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    # Public profile — /users/<pk>/profile/
    path(
        "<int:pk>/profile/",
        views.ProfileView.as_view(),
        name="profile",
    ),
    # Authenticated: edit own profile — /users/profile/edit/
    path(
        "profile/edit/",
        views.EditProfileView.as_view(),
        name="edit-profile",
    ),
    # AJAX: heatmap data — /users/<pk>/heatmap/
    path(
        "<int:pk>/heatmap/",
        views.ActivityHeatmapView.as_view(),
        name="heatmap",
    ),
]
