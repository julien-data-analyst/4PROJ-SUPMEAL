from datetime import UTC, datetime

import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from planning.models import Planning, RecipePlanning
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    Step,
    Tag,
)
from tests.recipes.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

###############################################-
# Helpers to build recipes/steps/tags/ingredients
# without going through the write serializer.
###############################################-


def _make_recipe(
    *,
    creator: User,
    title: str,
    cooking_duration: str | None = None,
    cookbook: Cookbook | None = None,
) -> Recipe:
    recipe = Recipe(
        title=title, creator=creator, cooking_duration=cooking_duration, cookbook=cookbook
    )
    recipe.save()
    return recipe


def _add_step(recipe: Recipe, minutes: int, step_number: int = 1, type_: str = "prep") -> Step:
    step = Step(
        recipe=recipe,
        description=f"Step {step_number}",
        step_number=step_number,
        dury=datetime(2000, 1, 1, 0, minutes, 0, tzinfo=UTC),
        type=type_,
    )
    step.save()
    return step


def _add_tag(recipe: Recipe, name: str, type_: str = "repas") -> Tag:
    tag, _ = Tag.objects.get_or_create(name=name, defaults={"type": type_})  # pyright: ignore[reportAttributeAccessIssue]
    RecipeTag.objects.create(recipe=recipe, tag=tag)  # pyright: ignore[reportAttributeAccessIssue]
    return tag


def _add_ingredient(recipe: Recipe, name: str) -> Ingredient:
    ingredient, _ = Ingredient.objects.get_or_create(name=name)  # pyright: ignore[reportAttributeAccessIssue]
    RecipeIngredient.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=recipe, ingredient=ingredient, quantity=1, person_numbers=1
    )
    return ingredient


def _titles(response) -> list[str]:
    return [recipe["title"] for recipe in response.data["results"]]


def _schedule_in_planning(
    recipe: Recipe, planning: Planning, dayofweek: str = "lundi"
) -> RecipePlanning:
    return RecipePlanning.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=recipe, planning=planning, type="plat", lunch="midi", dayofweek=dayofweek
    )


###########################-
# Pagination and ordering
###########################-


def test_recipe_list_is_paginated_with_default_page_size_of_ten(
    auth_client: APIClient, regular_user: User
):
    """Test that the recipe list defaults to 10 results/page and reports the total page count."""
    for i in range(12):
        _make_recipe(creator=regular_user, title=f"Recipe {i}")
    url = reverse("recipe-list")

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["count"] == 12
    assert response.data["total_pages"] == 2
    assert response.data["current_page"] == 1
    assert len(response.data["results"]) == 10
    assert response.data["next"] is not None
    assert response.data["previous"] is None


def test_recipe_list_page_size_can_be_overridden(auth_client: APIClient, regular_user: User):
    """Test that ``?page_size=`` overrides the default of 10."""
    for i in range(5):
        _make_recipe(creator=regular_user, title=f"Recipe {i}")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"page_size": 2})

    assert response.data is not None
    assert response.data["count"] == 5
    assert response.data["total_pages"] == 3
    assert len(response.data["results"]) == 2


def test_recipe_list_is_ordered_by_most_recently_updated_first(
    auth_client: APIClient, regular_user: User
):
    """Test that recipes are always sorted most-recently-modified first."""
    first = _make_recipe(creator=regular_user, title="Created first")
    second = _make_recipe(creator=regular_user, title="Created second")
    url = reverse("recipe-list")

    response = auth_client.get(url)

    assert _titles(response) == [second.title, first.title]

    first.save()  # bumps `updated_at` via auto_now
    response = auth_client.get(url)

    assert _titles(response) == [first.title, second.title]


###############################################-
# name: case-insensitive substring match (ILIKE)
###############################################-


def test_name_filter_matches_recipe_title(auth_client: APIClient, regular_user: User):
    """Test that ``?name=`` matches a substring of the recipe title."""
    matching = _make_recipe(creator=regular_user, title="Crepes sucrees")
    _make_recipe(creator=regular_user, title="Salade de tomates")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"name": "crepes"})

    assert _titles(response) == [matching.title]


def test_name_filter_excludes_non_matching_titles(auth_client: APIClient, regular_user: User):
    """Test that an unrelated search term returns no results."""
    _make_recipe(creator=regular_user, title="Crepes sucrees")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"name": "quiche"})

    assert _titles(response) == []


def test_name_filter_matches_single_letter_prefix(auth_client: APIClient, regular_user: User):
    """A single-letter query must still match (full-text search wouldn't)."""
    matching = _make_recipe(creator=regular_user, title="Gateaux au chocolat")
    _make_recipe(creator=regular_user, title="Salade de tomates")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"name": "G"})

    assert _titles(response) == [matching.title]


def test_name_filter_is_case_insensitive(auth_client: APIClient, regular_user: User):
    """Test that ``?name=`` ignores case."""
    matching = _make_recipe(creator=regular_user, title="Gateaux au chocolat")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"name": "GATEAUX"})

    assert _titles(response) == [matching.title]


##################################-
# tags / ingredients: AND semantics
##################################-


def test_tags_filter_requires_all_given_tags(auth_client: APIClient, regular_user: User):
    """Test that ``?tags=a,b`` only matches recipes carrying *every* given tag."""
    both = _make_recipe(creator=regular_user, title="Has both tags")
    only_one = _make_recipe(creator=regular_user, title="Has one tag")
    _add_tag(both, "Vegan")
    _add_tag(both, "Rapide")
    _add_tag(only_one, "Vegan")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"tags": "Vegan,Rapide"})

    assert _titles(response) == [both.title]


def test_tags_filter_accepts_ids(auth_client: APIClient, regular_user: User):
    """Test that tags can be selected by id, not just by name."""
    recipe = _make_recipe(creator=regular_user, title="Tagged recipe")
    tag = _add_tag(recipe, "Vegan")
    other_recipe = _make_recipe(creator=regular_user, title="Untagged recipe")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"tags": str(tag.pk)})

    assert _titles(response) == [recipe.title]
    assert other_recipe.title not in _titles(response)


def test_ingredients_filter_requires_all_given_ingredients(
    auth_client: APIClient, regular_user: User
):
    """Test that ``?ingredients=a,b`` only matches recipes using *every* given ingredient."""
    both = _make_recipe(creator=regular_user, title="Has both ingredients")
    only_one = _make_recipe(creator=regular_user, title="Has one ingredient")
    _add_ingredient(both, "Farine")
    _add_ingredient(both, "Oeuf")
    _add_ingredient(only_one, "Farine")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"ingredients": "Farine,Oeuf"})

    assert _titles(response) == [both.title]


def test_ingredients_filter_accepts_ids(auth_client: APIClient, regular_user: User):
    """Test that ingredients can be selected by id, not just by name."""
    recipe = _make_recipe(creator=regular_user, title="With ingredient")
    ingredient = _add_ingredient(recipe, "Farine")
    other_recipe = _make_recipe(creator=regular_user, title="Without ingredient")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"ingredients": str(ingredient.pk)})

    assert _titles(response) == [recipe.title]
    assert other_recipe.title not in _titles(response)


##########################-
# cookbook / in_cookbook
##########################-


def test_cookbook_filter_matches_cookbook_name(
    auth_client: APIClient, regular_user: User, owned_cookbook: Cookbook
):
    """Test that ``?cookbook=`` filters by (partial, case-insensitive) cookbook name."""
    filed = _make_recipe(creator=regular_user, title="Filed recipe", cookbook=owned_cookbook)
    _make_recipe(creator=regular_user, title="Standalone recipe")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"cookbook": str(owned_cookbook.name).lower()[:5]})

    assert _titles(response) == [filed.title]


def test_in_cookbook_filter_true_and_false(
    auth_client: APIClient, regular_user: User, owned_cookbook: Cookbook
):
    """Test that ``?in_cookbook=`` filters recipes by whether they're filed into a cookbook."""
    filed = _make_recipe(creator=regular_user, title="Filed recipe", cookbook=owned_cookbook)
    standalone = _make_recipe(creator=regular_user, title="Standalone recipe")
    url = reverse("recipe-list")

    response_true = auth_client.get(url, {"in_cookbook": "true"})
    response_false = auth_client.get(url, {"in_cookbook": "false"})

    assert _titles(response_true) == [filed.title]
    assert _titles(response_false) == [standalone.title]


##########################-
# planning / in_planning
##########################-


def test_planning_filter_matches_planning_name(auth_client: APIClient, regular_user: User):
    """Test that ``?planning=`` filters by (partial, case-insensitive) planning name."""
    scheduled = _make_recipe(creator=regular_user, title="Scheduled recipe")
    _make_recipe(creator=regular_user, title="Unscheduled recipe")
    planning = Planning.objects.create(name="Semaine du 20 juillet", creator=regular_user)  # pyright: ignore[reportAttributeAccessIssue]
    _schedule_in_planning(scheduled, planning)
    url = reverse("recipe-list")

    response = auth_client.get(url, {"planning": "semaine"})

    assert _titles(response) == [scheduled.title]


def test_planning_filter_excludes_non_matching_planning_names(
    auth_client: APIClient, regular_user: User
):
    """Test that an unrelated planning name search term returns no results."""
    scheduled = _make_recipe(creator=regular_user, title="Scheduled recipe")
    planning = Planning.objects.create(name="Semaine du 20 juillet", creator=regular_user)  # pyright: ignore[reportAttributeAccessIssue]
    _schedule_in_planning(scheduled, planning)
    url = reverse("recipe-list")

    response = auth_client.get(url, {"planning": "aout"})

    assert _titles(response) == []


def test_in_planning_filter_true_and_false(auth_client: APIClient, regular_user: User):
    """Test that ``?in_planning=`` filters recipes by whether they're scheduled in a planning."""
    scheduled = _make_recipe(creator=regular_user, title="Scheduled recipe")
    unscheduled = _make_recipe(creator=regular_user, title="Unscheduled recipe")
    planning = Planning.objects.create(name="Semaine du 20 juillet", creator=regular_user)  # pyright: ignore[reportAttributeAccessIssue]
    _schedule_in_planning(scheduled, planning)
    url = reverse("recipe-list")

    response_true = auth_client.get(url, {"in_planning": "true"})
    response_false = auth_client.get(url, {"in_planning": "false"})

    assert _titles(response_true) == [scheduled.title]
    assert _titles(response_false) == [unscheduled.title]


def test_planning_filter_does_not_duplicate_recipe_scheduled_multiple_times(
    auth_client: APIClient, regular_user: User
):
    """A recipe scheduled several times in the same planning must appear only once."""
    recipe = _make_recipe(creator=regular_user, title="Scheduled twice")
    planning = Planning.objects.create(name="Semaine du 20 juillet", creator=regular_user)  # pyright: ignore[reportAttributeAccessIssue]
    _schedule_in_planning(recipe, planning, dayofweek="lundi")
    _schedule_in_planning(recipe, planning, dayofweek="mardi")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"planning": "semaine"})

    assert _titles(response) == [recipe.title]


##########################################-
# shared_with_me: cookbooks shared with the caller
##########################################-


def test_shared_with_me_filter_true_returns_only_recipes_from_cookbooks_shared_with_caller(
    auth_client: APIClient,
    regular_user: User,
    owned_cookbook: Cookbook,
    cookbook_shared_with_regular_user: Cookbook,
):
    """Test that ``?shared_with_me=true`` only returns recipes filed in a cookbook shared
    with the caller - not their own cookbooks, and not standalone recipes.
    """
    _make_recipe(creator=regular_user, title="Dans mon carnet", cookbook=owned_cookbook)
    shared = _make_recipe(
        creator=regular_user,
        title="Dans un carnet partage",
        cookbook=cookbook_shared_with_regular_user,
    )
    _make_recipe(creator=regular_user, title="Recette autonome")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"shared_with_me": "true"})

    assert _titles(response) == [shared.title]


def test_shared_with_me_filter_false_excludes_recipes_from_cookbooks_shared_with_caller(
    auth_client: APIClient,
    regular_user: User,
    owned_cookbook: Cookbook,
    cookbook_shared_with_regular_user: Cookbook,
):
    """Test that ``?shared_with_me=false`` excludes recipes filed in a cookbook shared
    with the caller, keeping their own cookbooks and standalone recipes.
    """
    own = _make_recipe(creator=regular_user, title="Dans mon carnet", cookbook=owned_cookbook)
    _make_recipe(
        creator=regular_user,
        title="Dans un carnet partage",
        cookbook=cookbook_shared_with_regular_user,
    )
    standalone = _make_recipe(creator=regular_user, title="Recette autonome")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"shared_with_me": "false"})

    assert set(_titles(response)) == {own.title, standalone.title}


####################################-
# prep_time (sum of step durations)
####################################-


def test_prep_time_filters_use_the_sum_of_step_durations(
    auth_client: APIClient, regular_user: User
):
    """Test that prep time is the sum of a recipe's step durations, in minutes."""
    long_prep = _make_recipe(creator=regular_user, title="Long prep")
    _add_step(long_prep, minutes=5, step_number=1)
    _add_step(long_prep, minutes=10, step_number=2)  # total: 15 minutes
    short_prep = _make_recipe(creator=regular_user, title="Short prep")
    _add_step(short_prep, minutes=3, step_number=1)  # total: 3 minutes
    url = reverse("recipe-list")

    response_min = auth_client.get(url, {"prep_time_min": 10})
    response_max = auth_client.get(url, {"prep_time_max": 5})

    assert _titles(response_min) == [long_prep.title]
    assert _titles(response_max) == [short_prep.title]


def test_prep_time_filter_treats_recipe_without_steps_as_zero(
    auth_client: APIClient, regular_user: User
):
    """Test that a recipe with no steps counts as 0 minutes of prep time."""
    _make_recipe(creator=regular_user, title="No steps")
    url = reverse("recipe-list")

    response = auth_client.get(url, {"prep_time_min": 1})

    assert _titles(response) == []


#########################-
# cooking_duration range
#########################-


def test_cooking_duration_filters(auth_client: APIClient, regular_user: User):
    """Test that ``?cooking_duration_min=``/``?cooking_duration_max=`` filter on that field."""
    slow = _make_recipe(creator=regular_user, title="Slow", cooking_duration="45.00")
    fast = _make_recipe(creator=regular_user, title="Fast", cooking_duration="5.00")
    url = reverse("recipe-list")

    response_min = auth_client.get(url, {"cooking_duration_min": 30})
    response_max = auth_client.get(url, {"cooking_duration_max": 10})

    assert _titles(response_min) == [slow.title]
    assert _titles(response_max) == [fast.title]


##################################-
# favorite: filter + POST/DELETE
##################################-


def test_favorite_filter_returns_only_the_callers_favorites(
    auth_client: APIClient, regular_user: User
):
    """Test that ``?favorite=true``/``?favorite=false`` filters by the caller's own favorites."""
    favorite = _make_recipe(creator=regular_user, title="Favorited")
    not_favorite = _make_recipe(creator=regular_user, title="Not favorited")
    FavoriteRecipe.objects.create(user=regular_user, recipe=favorite)  # pyright: ignore[reportAttributeAccessIssue]
    url = reverse("recipe-list")

    response_true = auth_client.get(url, {"favorite": "true"})
    response_false = auth_client.get(url, {"favorite": "false"})

    assert _titles(response_true) == [favorite.title]
    assert _titles(response_false) == [not_favorite.title]


def test_recipe_serializer_exposes_is_favorite(auth_client: APIClient, regular_user: User):
    """Test that each recipe reports whether the caller has favorited it."""
    recipe = _make_recipe(creator=regular_user, title="Maybe favorite")
    url = reverse("recipe-detail", kwargs={"pk": recipe.pk})

    response = auth_client.get(url)
    assert response.data is not None
    assert response.data["is_favorite"] is False

    FavoriteRecipe.objects.create(user=regular_user, recipe=recipe)  # pyright: ignore[reportAttributeAccessIssue]

    response = auth_client.get(url)
    assert response.data is not None
    assert response.data["is_favorite"] is True


def test_post_favorite_adds_recipe_to_callers_favorites(
    auth_client: APIClient, regular_user: User, owned_recipe: Recipe
):
    """Test that ``POST .../favorite/`` marks the recipe as a favorite for the caller."""
    url = reverse("recipe-favorite", kwargs={"pk": owned_recipe.pk})

    response = auth_client.post(url)

    assert response.status_code == status.HTTP_201_CREATED
    assert FavoriteRecipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        user=regular_user, recipe=owned_recipe
    ).exists()


def test_post_favorite_twice_is_idempotent(
    auth_client: APIClient, regular_user: User, owned_recipe: Recipe
):
    """Test that favoriting an already-favorited recipe doesn't error or duplicate the row."""
    url = reverse("recipe-favorite", kwargs={"pk": owned_recipe.pk})
    auth_client.post(url)

    response = auth_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    assert (
        FavoriteRecipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            user=regular_user, recipe=owned_recipe
        ).count()
        == 1
    )


def test_delete_favorite_removes_recipe_from_callers_favorites(
    auth_client: APIClient, regular_user: User, owned_recipe: Recipe
):
    """Test that ``DELETE .../favorite/`` un-favorites the recipe for the caller."""
    FavoriteRecipe.objects.create(user=regular_user, recipe=owned_recipe)  # pyright: ignore[reportAttributeAccessIssue]
    url = reverse("recipe-favorite", kwargs={"pk": owned_recipe.pk})

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FavoriteRecipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        user=regular_user, recipe=owned_recipe
    ).exists()


def test_delete_favorite_on_non_favorited_recipe_is_a_no_op(
    auth_client: APIClient, owned_recipe: Recipe
):
    """Test that un-favoriting a recipe that isn't a favorite is a no-op, not an error."""
    url = reverse("recipe-favorite", kwargs={"pk": owned_recipe.pk})

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_anonymous_user_cannot_favorite_a_recipe(api_client: APIClient, owned_recipe: Recipe):
    """Test that favoriting requires authentication."""
    url = reverse("recipe-favorite", kwargs={"pk": owned_recipe.pk})

    response = api_client.post(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not FavoriteRecipe.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]
