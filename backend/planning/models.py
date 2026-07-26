from django.conf import settings
from django.db import models

from cookbooks.models import Cookbook
from recipes.models import Recipe

# Hard-coded default icon (a plain SVG, base64-encoded as a data URI) used for
# every planning that doesn't set its own - not part of the original SQL
# schema (``docs/database.md``), added on top of it purely for display.
DEFAULT_PLANNING_ICON = (
    "data:image/svg+xml;base64,"
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0i"
    "IzNCNkU4RiI+PHBhdGggZD0iTTcgMnYySDVhMiAyIDAgMCAwLTIgMnYxNGEyIDIgMCAwIDAgMiAyaDE0YTIgMiAw"
    "IDAgMCAyLTJWNmEyIDIgMCAwIDAtMi0yaC0yVjJoLTJ2Mkg5VjJIN3pNNSA5aDE0djExSDVWOXoiLz48L3N2Zz4="
)


class Planning(models.Model):
    """A named meal plan created by a user (the schema's ``planning`` table).

    Optionally scoped to a ``Cookbook`` (nullable, like ``Recipe.cookbook``);
    the actual recipes assigned to the plan live on ``RecipePlanning``.
    """

    name = models.CharField(max_length=255)
    icon = models.TextField(  # noqa: DJ001 (nullable, optional)
        blank=True, null=True, default=DEFAULT_PLANNING_ICON
    )
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
    """Schedules a ``Recipe`` within a ``Planning``, for a given slot.

    Maps the schema's ``recipe_planning`` table. Unlike the schema's other
    join tables this uses a plain surrogate ``id`` rather than a composite
    primary key on ``(recipe, planning)``: the same recipe must be
    schedulable more than once in a planning (e.g. the same dessert on
    several days), so ``recipe``/``planning`` can't be the key on their
    own. Instead, a slot - ``(planning, dayofweek, lunch, type)`` - is kept
    unique, so at most one recipe fills a given day/meal-moment/course.
    ``type``/``lunch``/``dayofweek`` are free text in the schema
    (``dayofweek`` being optional there).
    """

    recipe = models.ForeignKey(Recipe, on_delete=models.PROTECT, related_name="recipe_plannings")
    planning = models.ForeignKey(
        Planning, on_delete=models.PROTECT, related_name="recipe_plannings"
    )
    type = models.CharField(max_length=50)
    lunch = models.CharField(max_length=50)
    dayofweek = models.CharField(max_length=20, blank=True, null=True)  # noqa: DJ001
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["planning", "dayofweek", "lunch", "type"],
                name="unique_recipe_planning_slot",
            )
        ]

    def __str__(self) -> str:
        return f"{self.recipe} - {self.planning}"
