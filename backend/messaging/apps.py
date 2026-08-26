from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """Configuration for the ``messaging`` app.

    Holds the ``Message`` model used for cookbook/recipe chat threads.
    """

    default_auto_field = "django.db.models.BigAutoField"  # pyright: ignore[reportAssignmentType]
    name = "messaging"
