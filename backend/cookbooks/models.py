from django.conf import settings
from django.db import models


class Cookbook(models.Model):
    """A collection of recipes owned by a user (the schema's ``cookbook`` table).

    A cookbook can be shared with other users through ``SharedUserCookbook``,
    and groups together recipes, plannings and messages.
    """

    name = models.CharField(max_length=255)
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
