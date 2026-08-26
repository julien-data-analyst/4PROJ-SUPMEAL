"""Build the portable JSON representation of a cookbook, for export.

Used by ``CookbookViewSet``'s ``export``/``export_list`` actions (see
``cookbooks/views.py``). Embeds every recipe filed into the cookbook using
``recipes.export.export_recipe`` (the same shape used for standalone
recipe export), each one tagged with its export-local ``id``. That id is
only a link key *within this JSON payload* - it lets ``plannings[].meals[]``
reference which recipe a scheduled meal is for, since a fresh import
creates brand-new recipe rows with new database ids (see
``cookbooks/imports.py``). Cookbook members (``shared_with``) are
intentionally never exported.

A planning's meal is only included if it schedules one of the cookbook's
own recipes (``recipe.cookbook == cookbook``) - a meal scheduling a recipe
filed elsewhere has nothing to link to in ``recipes[]`` and is dropped.
"""

from rest_framework import serializers

from recipes.export import RecipeExportSerializer, export_recipe

from .models import Cookbook


def export_cookbook(cookbook: Cookbook) -> dict:
    """Return the portable JSON representation of a single cookbook."""
    recipes = list(cookbook.recipes.all())  # pyright: ignore[reportAttributeAccessIssue]
    recipe_ids = {recipe.id for recipe in recipes}  # pyright: ignore[reportAttributeAccessIssue]

    recipes_data = []
    for recipe in recipes:
        data = export_recipe(recipe)
        data["id"] = recipe.id  # pyright: ignore[reportAttributeAccessIssue]
        recipes_data.append(data)

    plannings_data = []
    for planning in cookbook.plannings.all():  # pyright: ignore[reportAttributeAccessIssue]
        meals = [
            {
                "recipe_id": meal.recipe_id,
                "type": meal.type,
                "lunch": meal.lunch,
                "dayofweek": meal.dayofweek,
            }
            for meal in planning.recipe_plannings.all()  # pyright: ignore[reportAttributeAccessIssue]
            if meal.recipe_id in recipe_ids
        ]
        plannings_data.append({"name": planning.name, "icon": planning.icon, "meals": meals})

    return {
        "name": cookbook.name,
        "icon": cookbook.icon,
        "recipes": recipes_data,
        "plannings": plannings_data,
    }


def export_cookbooks(cookbooks) -> list[dict]:
    """Return the portable JSON representation of a list/queryset of cookbooks."""
    return [export_cookbook(cookbook) for cookbook in cookbooks]


class CookbookExportRecipeSerializer(RecipeExportSerializer):
    """A recipe within a cookbook export, with its export-local link ``id``."""

    id = serializers.IntegerField(
        help_text="Local id linking this recipe to plannings[].meals[].recipe_id "
        "within this same payload. Not a database id."
    )


class CookbookExportMealSerializer(serializers.Serializer):
    """One scheduled meal within a cookbook export's plannings[].meals[]."""

    recipe_id = serializers.IntegerField(help_text="Matches one of recipes[].id above.")
    type = serializers.CharField()
    lunch = serializers.CharField()
    dayofweek = serializers.CharField(allow_null=True)


class CookbookExportPlanningSerializer(serializers.Serializer):
    """One planning within a cookbook export's plannings[]."""

    name = serializers.CharField()
    icon = serializers.CharField(allow_null=True)
    meals = CookbookExportMealSerializer(many=True)


class CookbookExportSerializer(serializers.Serializer):
    """Documents the shape returned by ``export_cookbook``/``export_cookbooks``.

    Not used to build the actual response (``export_cookbook`` returns
    plain dicts, serialized as-is) - this class only feeds drf-spectacular
    so the OpenAPI schema/Swagger UI accurately describes the export
    payload.
    """

    name = serializers.CharField()
    icon = serializers.CharField(allow_null=True)
    recipes = CookbookExportRecipeSerializer(many=True)
    plannings = CookbookExportPlanningSerializer(many=True)
