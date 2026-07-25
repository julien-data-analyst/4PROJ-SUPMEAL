from django.conf import settings
from django.db import models

from cookbooks.models import Cookbook
from recipes.models import Recipe


class Message(models.Model):
    """A chat message posted by a user in the context of a cookbook/recipe.

    Maps the schema's ``message`` table. ``canal`` identifies the
    conversation channel (free text in the schema); messages are always
    tied to both a ``Cookbook`` and a ``Recipe`` and are ordered
    chronologically (see ``Meta.ordering``).
    """

    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="messages"
    )
    canal = models.CharField(max_length=50)
    cookbook = models.ForeignKey(Cookbook, on_delete=models.PROTECT, related_name="messages")
    recipe = models.ForeignKey(Recipe, on_delete=models.PROTECT, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.author} @ {self.created_at:%Y-%m-%d %H:%M}"
