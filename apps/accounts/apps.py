from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name  = 'apps.accounts'
    label = 'accounts'          # short label used by Django internally

    def ready(self):
        import apps.accounts.signals  # noqa — register signal handlers