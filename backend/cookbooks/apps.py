from django.apps import AppConfig


class CookbooksConfig(AppConfig):
    """Configuration for the ``cookbooks`` app.

    Holds the ``Cookbook`` model and the user-sharing join table
    (``SharedUserCookbook``).
    """

    default_auto_field = "django.db.models.BigAutoField"  # pyright: ignore[reportAssignmentType]
    name = "cookbooks"
