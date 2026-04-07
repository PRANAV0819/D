from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User, Profile, UserSkill


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Auto-create a Profile whenever a new User is saved."""
    if created:
        Profile.objects.get_or_create(user=instance)


# ── AI Embedding signals ───────────────────────────────────────────────

@receiver(post_save, sender=UserSkill)
def on_skill_added(sender, instance, **kwargs):
    """
    When a skill is added or updated, recompute the user's embedding
    asynchronously so the mentor matching stays fresh.
    """
    try:
        from apps.mentorship.ai_matching import async_compute_embedding
        async_compute_embedding(instance.profile)
    except Exception:
        pass  # Never break the save if embedding fails


@receiver(post_delete, sender=UserSkill)
def on_skill_removed(sender, instance, **kwargs):
    """
    When a skill is removed, recompute the user's embedding.
    """
    try:
        from apps.mentorship.ai_matching import async_compute_embedding
        async_compute_embedding(instance.profile)
    except Exception:
        pass