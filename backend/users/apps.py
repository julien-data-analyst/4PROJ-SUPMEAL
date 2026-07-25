from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuration for the ``users`` app.

    Holds the custom ``User`` model (set as ``AUTH_USER_MODEL`` in
    settings.py) and the OAuth identities linked to it.
    """

    default_auto_field = "django.db.models.BigAutoField"  # pyright: ignore[reportAssignmentType]
    name = "users"
