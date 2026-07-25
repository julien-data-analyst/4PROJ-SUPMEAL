from django.conf import settings
from django.db import models

from cookbooks.models import Cookbook


class Ingredient(models.Model):
    """A reusable ingredient (e.g. "flour", "egg") shared across recipes.

    Maps the schema's ``ingredient`` table. The actual quantity used in a
    given recipe lives on the ``RecipeIngredient`` join table, not here.
    """

    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)


class Tag(models.Model):
    """A label used to categorize recipes (e.g. diet, cuisine, difficulty).

    Maps the schema's ``tag`` table. ``type`` distinguishes tag categories
    (free text, no fixed choices in the schema). Tags are attached to
    recipes via ``RecipeTag`` and can also express a user's taste through
    ``UserPreference``.
    """

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)  # noqa: DJ001 (nullable in schema)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)


class Recipe(models.Model):
    """A recipe: title, optional source/image, steps, ingredients and tags.

    Maps the schema's ``recipe`` table. ``cookbook`` is nullable because a
    recipe can exist on its own before being filed into a cookbook.
    """

    title = models.CharField(max_length=255)
    image = models.TextField(blank=True, null=True)  # noqa: DJ001 (nullable in schema)
    source = models.TextField(blank=True, null=True)  # noqa: DJ001 (nullable in schema)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recipes"
    )
    cookbook = models.ForeignKey(
        Cookbook,
        on_delete=models.PROTECT,
        related_name="recipes",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.title)


class RecipeIngredient(models.Model):
    """Join table quantifying how much of an ingredient a recipe needs.

    Maps the schema's ``recipe_ingredient`` table. Uses a composite primary
    key on ``(recipe, ingredient)``: a recipe lists a given ingredient at
    most once, with its ``quantity``/``unity`` for ``person_numbers`` people.
    """

    pk = models.CompositePrimaryKey("recipe", "ingredient")
    recipe = models.ForeignKey(
        Recipe, on_delete=models.PROTECT, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name="recipe_ingredients"
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unity = models.CharField(max_length=50, blank=True, null=True)  # noqa: DJ001 (nullable in schema)
    person_numbers = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.ingredient} - {self.recipe}"


class RecipeTag(models.Model):
    """Join table attaching a ``Tag`` to a ``Recipe``.

    Maps the schema's ``recipe_tag`` table. Composite primary key on
    ``(recipe, tag)`` so a recipe can't carry the same tag twice.
    """

    pk = models.CompositePrimaryKey("recipe", "tag")
    recipe = models.ForeignKey(Recipe, on_delete=models.PROTECT, related_name="recipe_tags")
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT, related_name="recipe_tags")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.tag} - {self.recipe}"


class UserPreference(models.Model):
    """Join table recording that a user likes/follows a given ``Tag``.

    Maps the schema's ``user_preferences`` table. Lives in the ``recipes``
    app (next to ``Tag``) rather than in ``users``, so that the ``users``
    app never depends on ``recipes`` - see the "Circular app dependencies"
    note in docs/database.md for why that matters with composite primary
    keys. Composite primary key on ``(user, tag)``.
    """

    pk = models.CompositePrimaryKey("user", "tag")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="preferences"
    )
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT, related_name="user_preferences")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} - {self.tag}"


class Step(models.Model):
    """A single, ordered instruction step of a recipe.

    Maps the schema's ``step`` table. ``step_number`` gives the order within
    the recipe (see ``Meta.ordering``); ``dury`` mirrors the schema's
    ``TIMESTAMP`` column for the step's duration/time and ``type`` is free
    text (e.g. "prep", "cook").
    """

    description = models.TextField()
    step_number = models.PositiveIntegerField()
    dury = models.DateTimeField()
    type = models.CharField(max_length=50)
    recipe = models.ForeignKey(Recipe, on_delete=models.PROTECT, related_name="steps")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["recipe", "step_number"]

    def __str__(self) -> str:
        return f"{self.recipe} - step {self.step_number}"
