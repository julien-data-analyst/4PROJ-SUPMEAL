from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model used as ``AUTH_USER_MODEL`` for the whole project.

    Extends Django's built-in ``AbstractUser`` (which already provides
    ``username``, ``first_name``, ``last_name``, ``password``, permissions,
    etc.) with the extra fields required by the SQL schema's ``user`` table:
    ``email`` (made unique), ``profile_icon``, ``created_at`` and
    ``updated_at``. Authentication itself (password or OAuth) is handled by
    django-allauth / dj-rest-auth on top of this model.
    """

    email = models.EmailField(unique=True)
    profile_icon = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.get_full_name() or self.username)


class OAuthUser(models.Model):
    """An external OAuth identity (Google, GitHub, ...) linked to a ``User``.

    Maps the schema's ``OAuth_user`` table. A single ``User`` can have
    several ``OAuthUser`` rows (one per provider), hence the plain
    ``ForeignKey`` (not one-to-one).
    """

    provider = models.CharField(max_length=100)
    provider_url = models.URLField(max_length=255)
    profile_icon = models.TextField(blank=True, null=True)  # noqa: DJ001 (nullable in schema)
    domain = models.CharField(max_length=255)
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="oauth_accounts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.provider} ({self.user})"
