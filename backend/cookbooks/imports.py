"""Create cookbooks from their portable JSON export (see ``cookbooks/export.py``).

Used by ``CookbookViewSet.import_data`` (see ``cookbooks/views.py``).
Accepts either a single cookbook object or a list of them. The
authenticated user becomes the creator (and implicit admin) of every
cookbook created this way; nested recipes are filed into the new cookbook
and nested plannings are rebuilt by resolving each meal's ``recipe_id``
against the ``id`` carried by ``recipes[]`` in the *same* payload item -
see ``cookbooks/export.py`` for why that link exists. Cookbook members are
never imported - a fresh cookbook only ever has its creator.
"""

from django.db import transaction
from rest_framework import serializers

from planning.models import Planning, RecipePlanning
from planning.serializers import DAYS_OF_WEEK, MEAL_COURSES, MEAL_MOMENTS
from recipes.models import Recipe
from recipes.serializers import (
    RecipeIngredientItemSerializer,
    RecipeTagItemSerializer,
    StepSerializer,
)
from recipes.services import sync_recipe_ingredients, sync_recipe_steps, sync_recipe_tags

from .models import Cookbook


class CookbookImportRecipeSerializer(serializers.Serializer):
    """One recipe within a cookbook import payload, carrying its link ``id``."""

    id = serializers.IntegerField(
        help_text="Local id linking this recipe to plannings[].meals[].recipe_id "
        "within this same payload item. Not a database id."
    )
    title = serializers.CharField(max_length=255)
    image = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    source = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    cooking_duration = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, allow_null=True
    )
    tags = RecipeTagItemSerializer(many=True, required=False)
    ingredients = RecipeIngredientItemSerializer(many=True, required=False)
    steps = StepSerializer(many=True, required=False)


class CookbookImportMealSerializer(serializers.Serializer):
    """One scheduled meal within a cookbook import's plannings[].meals[]."""

    recipe_id = serializers.IntegerField(
        help_text="Must match the `id` of one of this payload item's recipes[]."
    )
    type = serializers.ChoiceField(choices=MEAL_COURSES)
    lunch = serializers.ChoiceField(choices=MEAL_MOMENTS)
    dayofweek = serializers.ChoiceField(choices=DAYS_OF_WEEK, required=False, allow_null=True)


class CookbookImportPlanningSerializer(serializers.Serializer):
    """One planning within a cookbook import payload."""

    name = serializers.CharField(max_length=255)
    icon = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    meals = CookbookImportMealSerializer(many=True, required=False)

    def validate_meals(self, meals: list[dict]) -> list[dict]:
        # Mirrors PlanningWriteSerializer.validate_meals: at most one recipe
        # per (dayofweek, lunch, type) slot, matching the model's own
        # ``unique_recipe_planning_slot`` constraint - checked here so a bad
        # payload fails validation instead of a raw IntegrityError.
        seen_slots = set()
        for meal in meals:
            slot = (meal.get("dayofweek"), meal["lunch"], meal["type"])
            if slot in seen_slots:
                raise serializers.ValidationError(
                    f"Only one recipe can be scheduled for {meal.get('dayofweek')} "
                    f"{meal['lunch']} {meal['type']}."
                )
            seen_slots.add(slot)
        return meals


class CookbookImportSerializer(serializers.Serializer):
    """Validates one cookbook object from an import payload."""

    name = serializers.CharField(max_length=255)
    icon = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    recipes = CookbookImportRecipeSerializer(many=True, required=False)
    plannings = CookbookImportPlanningSerializer(many=True, required=False)

    def validate(self, attrs: dict) -> dict:
        recipe_ids = [item["id"] for item in attrs.get("recipes", [])]
        if len(recipe_ids) != len(set(recipe_ids)):
            raise serializers.ValidationError("recipes[].id must be unique within a cookbook.")

        known_ids = set(recipe_ids)
        for planning in attrs.get("plannings", []):
            for meal in planning.get("meals", []):
                if meal["recipe_id"] not in known_ids:
                    raise serializers.ValidationError(
                        f"plannings[].meals[].recipe_id {meal['recipe_id']} does not match "
                        "any recipes[].id in this payload."
                    )
        return attrs


def _create_cookbook(data: dict, user) -> Cookbook:
    # `icon` is only passed through when present in the payload, so a
    # cookbook/planning imported without one still falls back to the
    # model's own default icon (DEFAULT_COOKBOOK_ICON/DEFAULT_PLANNING_ICON)
    # exactly like a normal (non-import) create would.
    cookbook = Cookbook.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        name=data["name"],
        creator=user,
        **({"icon": data["icon"]} if "icon" in data else {}),
    )

    recipe_map: dict[int, Recipe] = {}
    for item in data.get("recipes", []):
        recipe = Recipe.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
            creator=user,
            cookbook=cookbook,
            title=item["title"],
            image=item.get("image"),
            source=item.get("source"),
            cooking_duration=item.get("cooking_duration"),
        )
        sync_recipe_ingredients(recipe, item.get("ingredients", []))
        sync_recipe_tags(recipe, item.get("tags", []))
        sync_recipe_steps(recipe, item.get("steps", []))
        recipe_map[item["id"]] = recipe

    for planning_item in data.get("plannings", []):
        planning = Planning.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
            name=planning_item["name"],
            creator=user,
            cookbook=cookbook,
            **({"icon": planning_item["icon"]} if "icon" in planning_item else {}),
        )
        RecipePlanning.objects.bulk_create(  # pyright: ignore[reportAttributeAccessIssue]
            RecipePlanning(
                planning=planning,
                recipe=recipe_map[meal["recipe_id"]],
                type=meal["type"],
                lunch=meal["lunch"],
                dayofweek=meal.get("dayofweek"),
            )
            for meal in planning_item.get("meals", [])
        )

    return cookbook


def import_cookbooks(payload, user) -> list[Cookbook]:
    """Create one or more cookbooks from ``payload`` (a single object or a list).

    Raises ``rest_framework.exceptions.ValidationError`` if any item is
    invalid - in that case nothing is created (all-or-nothing).
    """
    items = payload if isinstance(payload, list) else [payload]
    serializer = CookbookImportSerializer(data=items, many=True)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
        return [
            _create_cookbook(item, user)
            for item in serializer.validated_data  # pyright: ignore[reportOptionalIterable, reportGeneralTypeIssues]
        ]
