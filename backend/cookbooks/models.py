from django.conf import settings
from django.db import models

# Hard-coded default icon (a plain SVG, base64-encoded as a data URI) used for
# every cookbook that doesn't set its own - not part of the original SQL
# schema (``docs/database.md``), added on top of it purely for display.
DEFAULT_COOKBOOK_ICON = (
    "data:image/svg+xml;base64,"
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0i"
    "IzZCNEYzQiI+PHBhdGggZD0iTTEyIDRDMTAgMi41IDYgMiAzIDN2MTVjMy0xIDctLjUgOSAxIDItMS41IDYtMiA5"
    "LTFWM2MtMy0xLTctLjUtOSAxeiIvPjwvc3ZnPg=="
)


class Cookbook(models.Model):
    """A collection of recipes owned by a user (the schema's ``cookbook`` table).

    A cookbook can be shared with other users through ``SharedUserCookbook``,
    and groups together recipes, plannings and messages.
    """

    name = models.CharField(max_length=255)
    icon = models.TextField(  # noqa: DJ001 (nullable, optional)
        blank=True, null=True, default=DEFAULT_COOKBOOK_ICON
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cookbooks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)


class SharedUserCookbook(models.Model):
    """Join table granting a user access to a cookbook they didn't create.

    Maps the schema's ``shared_user_cookbook`` table. Uses a composite
    primary key on ``(cookbook, user)`` since a user can only be shared a
    given cookbook once; ``role`` carries the permission level. The
    cookbook's own creator is always an implicit "admin" and is never
    represented as a row here - see ``cookbooks.permissions`` for the full
    role/rank model.
    """

    class Role(models.TextChoices):
        CREATOR = "creator", "Creator"  # pyright: ignore[reportAssignmentType]
        EDITOR = "editor", "Editor"  # pyright: ignore[reportAssignmentType]
        COMMENTATOR = "commentator", "Commentator"  # pyright: ignore[reportAssignmentType]
        READER = "reader", "Reader"  # pyright: ignore[reportAssignmentType]

    pk = models.CompositePrimaryKey("cookbook", "user")
    cookbook = models.ForeignKey(Cookbook, on_delete=models.PROTECT, related_name="shared_with")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="shared_cookbooks"
    )
    role = models.CharField(max_length=50, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user} - {self.cookbook} ({self.role})"
