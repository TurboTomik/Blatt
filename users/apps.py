from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self) -> None:
        """
        Initialize app when Django is ready.

        This imports the signals module to register signal handlers.
        """
        import users.signals  # noqa
