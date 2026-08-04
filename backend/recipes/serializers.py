from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from common.image_validation import validate_image_data_uri
from cookbooks.permissions import has_rank
from users.serializers import UserSerializer

from .models import Ingredient, Recipe, RecipeIngredient, Step, Tag
from .services import sync_recipe_ingredients, sync_recipe_steps, sync_recipe_tags


class IngredientSerializer(serializers.ModelSerializer):
    """Read-only representation of a shared ``Ingredient``."""

    class Meta:
        model = Ingredient
        fields = ["id", "name", "image", "created_at", "updated_at"]
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):
    """Read-only representation of a shared ``Tag`` (category/sub-category)."""

    class Meta:
        model = Tag
        fields = ["id", "name", "type", "description", "created_at", "updated_at"]
        read_only_fields = fields


class StepSerializer(serializers.ModelSerializer):
    """A recipe step. Steps belong to a single recipe, so unlike ingredients
    and tags they are never shared/reused - no get-or-create logic needed.
    """

    class Meta:
        model = Step
        fields = ["id", "description", "step_number", "dury", "type"]
        read_only_fields = ["id"]


class RecipeIngredientItemSerializer(serializers.Serializer):
    """Write payload for one ingredient line of a recipe.

    Flattens the shared ``Ingredient`` (``name``/``image``) and the
    per-recipe ``RecipeIngredient`` join fields (``quantity``/``unity``/
    ``person_numbers``) into a single object, matching how the frontend
    sends an ingredient line.
    """

    name = serializers.CharField(max_length=255)
    image = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    unity = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=True)
    person_numbers = serializers.IntegerField(min_value=1)


class RecipeTagItemSerializer(serializers.Serializer):
    """Write payload for one tag of a recipe.

    ``type`` is the tag's sub-category (e.g. "repas", "regime_alimentaire").
    It's only used when the tag doesn't already exist - an existing tag
    keeps its stored type/description and is simply linked to the recipe.
    """

    name = serializers.CharField(max_length=255)
    type = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Read-only representation of one ingredient line within a recipe."""

    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ["ingredient", "quantity", "unity", "person_numbers"]
        read_only_fields = fields


class RecipePlanningUsageSerializer(serializers.Serializer):
    """Minimal ``{id, name}`` of a planning that schedules a given recipe.

    Used only to warn the caller, before/at delete time, which plannings a
    recipe would be removed from - see ``RecipeSerializer.used_in_plannings``.
    """

    id = serializers.IntegerField()
    name = serializers.CharField()


class RecipeSerializer(serializers.ModelSerializer):
    """Read-only representation of a recipe, with its steps/ingredients/tags."""

    creator = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(source="recipe_ingredients", many=True, read_only=True)
    tags = serializers.SerializerMethodField()
    steps = StepSerializer(many=True, read_only=True)
    is_favorite = serializers.BooleanField(read_only=True, default=False)
    used_in_plannings = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "image",
            "source",
            "cooking_duration",
            "creator",
            "cookbook",
            "ingredients",
            "tags",
            "steps",
            "is_favorite",
            "used_in_plannings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(TagSerializer(many=True))
    def get_tags(self, obj: Recipe):
        recipe_tags = obj.recipe_tags.all()  # pyright: ignore[reportAttributeAccessIssue]
        tags = [recipe_tag.tag for recipe_tag in recipe_tags]
        return TagSerializer(tags, many=True).data

    @extend_schema_field(RecipePlanningUsageSerializer(many=True))
    def get_used_in_plannings(self, obj: Recipe):
        # Distinct plannings that schedule this recipe in at least one slot -
        # relies on `recipe_plannings__planning` being prefetched by the
        # viewset's queryset, so this doesn't add an N+1 query per recipe.
        seen: dict[int, str] = {}
        for recipe_planning in obj.recipe_plannings.all():  # pyright: ignore[reportAttributeAccessIssue]
            seen[recipe_planning.planning_id] = recipe_planning.planning.name
        return [{"id": planning_id, "name": name} for planning_id, name in seen.items()]


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Create/update a recipe together with its ingredients, tags and steps.

    Ingredients/tags are shared, reusable rows: for each one, an existing row
    is matched by name (case-insensitive) and just linked to the recipe;
    only a genuinely new name creates a new ``Ingredient``/``Tag`` row (using
    the submitted sub-category for tags). Steps belong exclusively to the
    recipe and are always (re)created from scratch.

    ``ingredients``/``tags``/``steps`` are optional so that a partial update
    which omits one of them leaves the existing rows untouched; passing an
    empty list clears it instead.
    """

    ingredients = RecipeIngredientItemSerializer(many=True, required=False)
    tags = RecipeTagItemSerializer(many=True, required=False)
    steps = StepSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "image",
            "source",
            "cooking_duration",
            "cookbook",
            "ingredients",
            "tags",
            "steps",
        ]
        read_only_fields = ["id"]

    def validate_image(self, value: str | None) -> str | None:
        validate_image_data_uri(value)
        return value

    def validate_cookbook(self, cookbook):
        if cookbook is None:
            return cookbook
        user = self.context["request"].user
        if not has_rank(user, cookbook, "creator"):
            raise serializers.ValidationError(
                "You do not have the required role (creator or admin) on this cookbook."
            )
        return cookbook

    def create(self, validated_data: dict) -> Recipe:
        ingredients_data = validated_data.pop("ingredients", [])
        tags_data = validated_data.pop("tags", [])
        steps_data = validated_data.pop("steps", [])
        request = self.context["request"]

        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            recipe = Recipe.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
                creator=request.user, **validated_data
            )
            sync_recipe_ingredients(recipe, ingredients_data)
            sync_recipe_tags(recipe, tags_data)
            sync_recipe_steps(recipe, steps_data)
        return recipe

    def update(self, instance: Recipe, validated_data: dict) -> Recipe:
        ingredients_data = validated_data.pop("ingredients", None)
        tags_data = validated_data.pop("tags", None)
        steps_data = validated_data.pop("steps", None)

        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            instance = super().update(instance, validated_data)
            if ingredients_data is not None:
                sync_recipe_ingredients(instance, ingredients_data)
            if tags_data is not None:
                sync_recipe_tags(instance, tags_data)
            if steps_data is not None:
                sync_recipe_steps(instance, steps_data)
        return instance

    def to_representation(self, instance: Recipe):  # pyright: ignore[reportIncompatibleMethodOverride]
        return RecipeSerializer(instance, context=self.context).data
