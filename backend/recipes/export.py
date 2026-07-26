"""Build the portable JSON representation of a recipe, for export.

Used by ``RecipeViewSet``'s ``export``/``export_list`` actions (see
``recipes/views.py``) and reused by ``cookbooks/export.py`` to embed
recipes inside a cookbook export. The shape produced here is exactly what
``recipes/imports.py`` expects back on import: it deliberately drops
``id``, ``creator`` and ``cookbook`` so a recipe becomes a standalone,
re-importable unit - tags/ingredients are exported by name only (matching
how they're re-linked/created on import), and steps carry every field
except their ``id``.
"""

from rest_framework import serializers

from .models import Recipe
from .serializers import RecipeIngredientItemSerializer, RecipeTagItemSerializer, StepSerializer


def export_recipe(recipe: Recipe) -> dict:
    """Return the portable JSON representation of a single recipe."""
    return {
        "title": recipe.title,
        "image": recipe.image,
        "source": recipe.source,
        "cooking_duration": recipe.cooking_duration,
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
        "tags": [
            {
                "name": recipe_tag.tag.name,
                "type": recipe_tag.tag.type,
                "description": recipe_tag.tag.description,
            }
            for recipe_tag in recipe.recipe_tags.all()  # pyright: ignore[reportAttributeAccessIssue]
        ],
        "ingredients": [
            {
                "name": recipe_ingredient.ingredient.name,
                "image": recipe_ingredient.ingredient.image,
                "quantity": recipe_ingredient.quantity,
                "unity": recipe_ingredient.unity,
                "person_numbers": recipe_ingredient.person_numbers,
            }
            for recipe_ingredient in recipe.recipe_ingredients.all()  # pyright: ignore[reportAttributeAccessIssue]
        ],
        "steps": [
            {
                "description": step.description,
                "step_number": step.step_number,
                "dury": step.dury,
                "type": step.type,
            }
            for step in recipe.steps.all()  # pyright: ignore[reportAttributeAccessIssue]
        ],
    }


def export_recipes(recipes) -> list[dict]:
    """Return the portable JSON representation of a list/queryset of recipes."""
    return [export_recipe(recipe) for recipe in recipes]


class RecipeExportSerializer(serializers.Serializer):
    """Documents the shape returned by ``export_recipe``/``export_recipes``.

    Not used to build the actual response (``export_recipe`` returns plain
    dicts, serialized as-is) - this class only feeds drf-spectacular so the
    OpenAPI schema/Swagger UI accurately describes the export payload.
    """

    title = serializers.CharField()
    image = serializers.CharField(allow_null=True)
    source = serializers.CharField(allow_null=True)
    cooking_duration = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    tags = RecipeTagItemSerializer(many=True)
    ingredients = RecipeIngredientItemSerializer(many=True)
    steps = StepSerializer(many=True)
