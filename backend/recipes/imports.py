"""Create recipes from their portable JSON export (see ``recipes/export.py``).

Used by ``RecipeViewSet.import_data`` (see ``recipes/views.py``). Accepts
either a single recipe object or a list of them; every recipe created this
way is always a personal recipe (``cookbook=None``) owned by the
authenticated user - even a recipe that was exported from inside a
cookbook lands outside any cookbook here, matching the "recettes
personnelles (en dehors des cookbooks)" bulk-export case. Ingredients/tags
are matched by name and reused if they already exist, exactly like
``RecipeWriteSerializer`` (see ``recipes/services.py``); ``created_at``/
``updated_at`` from the export are informational only and are not
reapplied - Django sets fresh values on creation.
"""

from django.db import transaction
from rest_framework import serializers

from .models import Recipe
from .serializers import RecipeIngredientItemSerializer, RecipeTagItemSerializer, StepSerializer
from .services import sync_recipe_ingredients, sync_recipe_steps, sync_recipe_tags


class RecipeImportSerializer(serializers.Serializer):
    """Validates one recipe object from an import payload."""

    title = serializers.CharField(max_length=255)
    image = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    source = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    cooking_duration = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, allow_null=True
    )
    tags = RecipeTagItemSerializer(many=True, required=False)
    ingredients = RecipeIngredientItemSerializer(many=True, required=False)
    steps = StepSerializer(many=True, required=False)


def _create_recipe(data: dict, user) -> Recipe:
    recipe = Recipe.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        creator=user,
        cookbook=None,
        title=data["title"],
        image=data.get("image"),
        source=data.get("source"),
        cooking_duration=data.get("cooking_duration"),
    )
    sync_recipe_ingredients(recipe, data.get("ingredients", []))
    sync_recipe_tags(recipe, data.get("tags", []))
    sync_recipe_steps(recipe, data.get("steps", []))
    return recipe


def import_recipes(payload, user) -> list[Recipe]:
    """Create one or more recipes from ``payload`` (a single object or a list).

    Raises ``rest_framework.exceptions.ValidationError`` if any item is
    invalid - in that case nothing is created (all-or-nothing).
    """
    items = payload if isinstance(payload, list) else [payload]
    serializer = RecipeImportSerializer(data=items, many=True)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
        return [
            _create_recipe(item, user)
            for item in serializer.validated_data  # pyright: ignore[reportOptionalIterable, reportGeneralTypeIssues]
        ]
