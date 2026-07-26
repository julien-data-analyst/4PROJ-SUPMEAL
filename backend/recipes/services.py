"""Shared creation helpers for a recipe's ingredients/tags/steps.

Used by both ``RecipeWriteSerializer`` (the normal create/update path) and
the import script in ``recipes/imports.py``, so the "get-or-create by name"
semantics for ingredients/tags - and the "replace all steps" semantics for
steps - stay in one place instead of being duplicated.
"""

from .models import Ingredient, Recipe, Step, Tag


def get_or_create_ingredient(name: str, image: str | None) -> Ingredient:
    ingredient = Ingredient.objects.filter(name__iexact=name).first()  # pyright: ignore[reportAttributeAccessIssue]
    if ingredient is None:
        ingredient = Ingredient.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
            name=name, image=image
        )
    return ingredient


def get_or_create_tag(name: str, tag_type: str, description: str | None) -> Tag:
    tag = Tag.objects.filter(name__iexact=name).first()  # pyright: ignore[reportAttributeAccessIssue]
    if tag is None:
        tag = Tag.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
            name=name, type=tag_type, description=description
        )
    return tag


def sync_recipe_ingredients(recipe: Recipe, items: list[dict]) -> None:
    """Replace ``recipe``'s ingredient lines with ``items``, reusing/creating
    the shared ``Ingredient`` rows by name (case-insensitive).
    """
    recipe.recipe_ingredients.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
    for item in items:
        ingredient = get_or_create_ingredient(item["name"], item.get("image"))
        recipe.recipe_ingredients.create(  # pyright: ignore[reportAttributeAccessIssue]
            ingredient=ingredient,
            quantity=item["quantity"],
            unity=item.get("unity"),
            person_numbers=item["person_numbers"],
        )


def sync_recipe_tags(recipe: Recipe, items: list[dict]) -> None:
    """Replace ``recipe``'s tags with ``items``, reusing/creating the shared
    ``Tag`` rows by name (case-insensitive).
    """
    recipe.recipe_tags.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
    for item in items:
        tag = get_or_create_tag(item["name"], item["type"], item.get("description"))
        recipe.recipe_tags.create(tag=tag)  # pyright: ignore[reportAttributeAccessIssue]


def sync_recipe_steps(recipe: Recipe, items: list[dict]) -> None:
    """Replace ``recipe``'s steps with ``items`` (steps are never shared/reused)."""
    recipe.steps.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
    Step.objects.bulk_create(  # pyright: ignore[reportAttributeAccessIssue]
        Step(recipe=recipe, **item) for item in items
    )
