from django.db import transaction
from rest_framework import serializers

from cookbooks.permissions import has_rank
from recipes.models import Recipe
from recipes.serializers import RecipeSerializer
from users.serializers import UserSerializer

from .models import Planning, RecipePlanning

MEAL_MOMENTS = ("midi", "soir")
MEAL_COURSES = ("entree", "plat", "dessert")
DAYS_OF_WEEK = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")


class RecipePlanningSerializer(serializers.ModelSerializer):
    """Read-only representation of one recipe scheduled within a planning."""

    recipe = RecipeSerializer(read_only=True)

    class Meta:
        model = RecipePlanning
        fields = ["recipe", "type", "lunch", "dayofweek"]
        read_only_fields = fields


class RecipePlanningItemSerializer(serializers.Serializer):
    """Write payload for one scheduled meal slot of a planning.

    A slot is identified by ``dayofweek`` + ``lunch`` (the meal moment,
    "midi"/"soir") + ``type`` (the course, "entree"/"plat"/"dessert") - at
    most one recipe per slot, giving up to 7 * 2 * 3 = 42 recipes a week.
    """

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())  # pyright: ignore[reportAttributeAccessIssue]
    dayofweek = serializers.ChoiceField(choices=DAYS_OF_WEEK)
    lunch = serializers.ChoiceField(choices=MEAL_MOMENTS)
    type = serializers.ChoiceField(choices=MEAL_COURSES)


class PlanningSerializer(serializers.ModelSerializer):
    """Read-only representation of a planning, with its scheduled meals."""

    creator = UserSerializer(read_only=True)
    meals = RecipePlanningSerializer(source="recipe_plannings", many=True, read_only=True)

    class Meta:
        model = Planning
        fields = ["id", "name", "creator", "cookbook", "meals", "created_at", "updated_at"]
        read_only_fields = fields


class PlanningWriteSerializer(serializers.ModelSerializer):
    """Create/update a planning together with its scheduled meals.

    The same recipe can be scheduled more than once in a planning (e.g. the
    same dessert on several days). What must stay unique is the *slot* -
    ``(dayofweek, lunch, type)`` - checked below rather than left to fail
    with a raw ``IntegrityError`` from the model's ``UniqueConstraint``.

    ``meals`` is optional so a partial update omitting it leaves the
    existing schedule untouched; passing an empty list clears it.
    """

    meals = RecipePlanningItemSerializer(many=True, required=False)

    class Meta:
        model = Planning
        fields = ["id", "name", "cookbook", "meals"]
        read_only_fields = ["id"]

    def validate_cookbook(self, cookbook):
        if cookbook is None:
            return cookbook
        user = self.context["request"].user
        if not has_rank(user, cookbook, "creator"):
            raise serializers.ValidationError(
                "You do not have the required role (creator or admin) on this cookbook."
            )
        return cookbook

    def validate_meals(self, meals: list[dict]) -> list[dict]:
        seen_slots = set()
        for meal in meals:
            slot = (meal["dayofweek"], meal["lunch"], meal["type"])
            if slot in seen_slots:
                raise serializers.ValidationError(
                    f"Only one recipe can be scheduled for {meal['dayofweek']} "
                    f"{meal['lunch']} {meal['type']}."
                )
            seen_slots.add(slot)
        return meals

    def create(self, validated_data: dict) -> Planning:
        meals_data = validated_data.pop("meals", [])
        request = self.context["request"]

        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            planning = Planning.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
                creator=request.user, **validated_data
            )
            self._sync_meals(planning, meals_data)
        return planning

    def update(self, instance: Planning, validated_data: dict) -> Planning:
        meals_data = validated_data.pop("meals", None)

        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            instance = super().update(instance, validated_data)
            if meals_data is not None:
                self._sync_meals(instance, meals_data)
        return instance

    @staticmethod
    def _sync_meals(planning: Planning, items: list[dict]) -> None:
        planning.recipe_plannings.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
        RecipePlanning.objects.bulk_create(  # pyright: ignore[reportAttributeAccessIssue]
            RecipePlanning(
                planning=planning,
                recipe=item["recipe"],
                type=item["type"],
                lunch=item["lunch"],
                dayofweek=item["dayofweek"],
            )
            for item in items
        )

    def to_representation(self, instance: Planning):  # pyright: ignore[reportIncompatibleMethodOverride]
        return PlanningSerializer(instance, context=self.context).data
