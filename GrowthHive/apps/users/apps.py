"""apps/users/apps.py"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    label = "users"

    def ready(self) -> None:
        # Import signals module so all @receiver decorators are registered
        import apps.users.signals  # noqa: F401
