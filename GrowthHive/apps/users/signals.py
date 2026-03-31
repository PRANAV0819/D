"""
apps/users/signals.py

Signal handlers that wire the User model to its dependents:

  post_save(User)  → create Profile + ActivityStats rows (OneToOne)
  user_logged_in   → update last_active_at + increment login counter

Why signals instead of overriding save()?
  - Keeps the User model clean (no knowledge of Profile/ActivityStats)
  - Works correctly when users are created via management commands,
    API, admin, or any third-party code
  - Easy to test in isolation by disconnecting signals in test setUp

Registration in apps.py (AppConfig.ready) keeps Django's app registry
safe — signals are connected exactly once at startup.
"""

import logging

from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ActivityEvent, ActivityStats, Profile, User, record_activity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auto-create Profile + ActivityStats when a User is first created
# ---------------------------------------------------------------------------


@receiver(post_save, sender=User)
def create_user_dependents(sender, instance: User, created: bool, **kwargs) -> None:
    """
    Fires after every User.save().
    On creation: build Profile and ActivityStats in a nested transaction
    so a partial failure doesn't leave orphaned rows.

    We check for existence before creating (get_or_create) to make this
    handler idempotent — safe to run even if somehow called twice.
    """
    if not created:
        return

    try:
        with transaction.atomic():
            Profile.objects.get_or_create(user=instance)
            ActivityStats.objects.get_or_create(user=instance)
            logger.info(
                "Created Profile + ActivityStats for user %s (pk=%s)",
                instance.email,
                instance.pk,
            )
    except Exception:
        # Log but do not swallow — let the outer transaction see the error
        logger.exception(
            "Failed to create Profile/ActivityStats for user %s", instance.email
        )
        raise


# ---------------------------------------------------------------------------
# Track login events
# ---------------------------------------------------------------------------


@receiver(user_logged_in)
def track_login(sender, request, user: User, **kwargs) -> None:
    """
    Increment login counter and record an ActivityEvent on every login.
    Uses record_activity() so the logic stays in one place.
    """
    try:
        record_activity(user, ActivityEvent.EventType.LOGIN)
    except Exception:
        # Activity tracking must never break the login flow
        logger.exception("Failed to record login activity for user %s", user.email)
