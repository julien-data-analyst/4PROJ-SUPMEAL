from django.conf import settings
from django.db import models

from cookbooks.models import Cookbook
from recipes.models import Recipe


class Planning(models.Model):
    """A named meal plan created by a user (the schema's ``planning`` table).

    Optionally scoped to a ``Cookbook`` (nullable, like ``Recipe.cookbook``);
    the actual recipes assigned to the plan live on ``RecipePlanning``.
    """

    name = models.CharField(max_length=255)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="plannings"
    )
    cookbook = models.ForeignKey(
        Cookbook,
        on_delete=models.PROTECT,
        related_name="plannings",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)


class RecipePlanning(models.Model):
    """Join table scheduling a ``Recipe`` within a ``Planning``.

    Maps the schema's ``recipe_planning`` table. Composite primary key on
    ``(recipe, planning)``; ``type``/``lunch``/``dayofweek`` describe when
    and for which meal the recipe is scheduled (all free text in the
    schema, ``dayofweek`` being optional).
    """

    pk = models.CompositePrimaryKey("recipe", "planning")
    recipe = models.ForeignKey(
        Recipe, on_delete=models.PROTECT, related_name="recipe_plannings"
    )
    planning = models.ForeignKey(
        Planning, on_delete=models.PROTECT, related_name="recipe_plannings"
    )
    type = models.CharField(max_length=50)
    lunch = models.CharField(max_length=50)
    dayofweek = models.CharField(max_length=20, blank=True, null=True)  # noqa: DJ001
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.recipe} - {self.planning}"
