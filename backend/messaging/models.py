from django.conf import settings
from django.db import models

from cookbooks.models import Cookbook
from planning.models import Planning
from recipes.models import Recipe


class Message(models.Model):
    """A chat message posted by a user in the context of a cookbook/recipe/planning.

    Maps the schema's ``message`` table. ``canal`` identifies the
    conversation channel (free text in the schema). A message is always
    tied to a ``Cookbook``; ``recipe``/``planning`` are nullable and mutually
    exclusive, so a message targets either the cookbook's global channel
    (both ``None``), a specific recipe's channel, or a specific planning's
    channel. Messages are ordered chronologically (see ``Meta.ordering``).
    """

    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="messages"
    )
    canal = models.CharField(max_length=50)
    cookbook = models.ForeignKey(Cookbook, on_delete=models.PROTECT, related_name="messages")
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.PROTECT,
        related_name="messages",
        blank=True,
        null=True,
    )
    planning = models.ForeignKey(
        Planning,
        on_delete=models.PROTECT,
        related_name="messages",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~(
                    models.Q(recipe__isnull=False) & models.Q(planning__isnull=False)
                ),
                name="message_not_both_recipe_and_planning",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.author} @ {self.created_at:%Y-%m-%d %H:%M}"
