import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Step, Tag
from tests.recipes.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

#####################################################-
# Tests for a recipe owner's create/update/delete access
#####################################################-


def test_owner_can_create_recipe_with_ingredients_tags_and_steps(
    auth_client: APIClient, regular_user: User, recipe_payload: dict
):
    """Test that creating a recipe also creates its ingredients, tags and steps."""
    url = reverse("recipe-list")

    response = auth_client.post(url, recipe_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["title"] == "Crepes"
    assert response.data["cooking_duration"] == "15.50"
    assert response.data["creator"]["id"] == regular_user.pk
    assert len(response.data["ingredients"]) == 2
    assert len(response.data["tags"]) == 2
    assert len(response.data["steps"]) == 2

    recipe = Recipe.objects.get(pk=response.data["id"])  # pyright: ignore[reportAttributeAccessIssue]
    assert recipe.creator_id == regular_user.pk
    assert Ingredient.objects.count() == 2  # pyright: ignore[reportAttributeAccessIssue]
    assert Tag.objects.count() == 2  # pyright: ignore[reportAttributeAccessIssue]
    assert Step.objects.filter(recipe=recipe).count() == 2  # pyright: ignore[reportAttributeAccessIssue]


def test_owner_can_create_recipe_without_optional_nested_fields(auth_client: APIClient):
    """Test that ingredients/tags/steps are optional when creating a recipe."""
    url = reverse("recipe-list")

    response = auth_client.post(url, {"title": "Simple"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["ingredients"] == []
    assert response.data["tags"] == []
    assert response.data["steps"] == []


def test_creating_recipe_reuses_existing_ingredient_case_insensitively(
    auth_client: APIClient, recipe_payload: dict
):
    """Test that an ingredient with a matching name (any case) is reused, not duplicated."""
    existing = Ingredient(name="Farine", image="https://img/farine.png")
    existing.save()
    url = reverse("recipe-list")
    recipe_payload["ingredients"] = [
        {"name": "farine", "quantity": "100.00", "unity": "g", "person_numbers": 2}
    ]

    response = auth_client.post(url, recipe_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert Ingredient.objects.count() == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert response.data["ingredients"][0]["ingredient"]["id"] == existing.pk
    assert response.data["ingredients"][0]["ingredient"]["image"] == "https://img/farine.png"


def test_creating_recipe_reuses_existing_tag_and_keeps_its_original_type(
    auth_client: APIClient, recipe_payload: dict
):
    """Test that an existing tag is linked as-is, ignoring a mismatched submitted type."""
    existing = Tag(name="Dessert", type="repas")
    existing.save()
    url = reverse("recipe-list")
    recipe_payload["tags"] = [{"name": "dessert", "type": "regime_alimentaire"}]

    response = auth_client.post(url, recipe_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert Tag.objects.count() == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert response.data["tags"][0]["id"] == existing.pk
    assert response.data["tags"][0]["type"] == "repas"


def test_owner_can_partial_update_title_without_touching_nested_data(
    auth_client: APIClient, owned_recipe: Recipe
):
    """Test that a partial update omitting ingredients/tags/steps leaves them untouched."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})

    response = auth_client.patch(url, {"title": "Renamed Recipe"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["title"] == "Renamed Recipe"
    assert len(response.data["ingredients"]) == 1
    assert len(response.data["tags"]) == 1
    assert len(response.data["steps"]) == 1


def test_owner_can_replace_ingredients_on_update(auth_client: APIClient, owned_recipe: Recipe):
    """Test that sending a new ingredients list replaces the old one for that recipe."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})
    old_ingredient_id = RecipeIngredient.objects.get(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=owned_recipe
    ).ingredient_id

    response = auth_client.patch(
        url,
        {
            "ingredients": [
                {"name": "Poivre", "quantity": "2.00", "unity": "g", "person_numbers": 2}
            ]
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert len(response.data["ingredients"]) == 1
    assert response.data["ingredients"][0]["ingredient"]["name"] == "Poivre"
    # The old ingredient is unlinked, not deleted - it's shared master data.
    assert Ingredient.objects.filter(pk=old_ingredient_id).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not RecipeIngredient.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=owned_recipe, ingredient_id=old_ingredient_id
    ).exists()


def test_owner_can_clear_tags_with_empty_list(auth_client: APIClient, owned_recipe: Recipe):
    """Test that sending an empty tags list removes all tags from the recipe."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})

    response = auth_client.patch(url, {"tags": []}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["tags"] == []
    assert Tag.objects.count() == 1  # pyright: ignore[reportAttributeAccessIssue]


def test_owner_can_replace_recipe_via_put_without_clearing_omitted_nested_fields(
    auth_client: APIClient, owned_recipe: Recipe
):
    """Test that a full PUT omitting ingredients/tags/steps still leaves them untouched."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})

    response = auth_client.put(url, {"title": "Fully Replaced"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["title"] == "Fully Replaced"
    assert len(response.data["ingredients"]) == 1
    assert len(response.data["tags"]) == 1
    assert len(response.data["steps"]) == 1


def test_owner_can_delete_own_recipe(auth_client: APIClient, owned_recipe: Recipe):
    """Test that deleting a recipe also removes its steps/ingredients/tags links."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})
    ingredient_id = RecipeIngredient.objects.get(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=owned_recipe
    ).ingredient_id
    tag_id = RecipeTag.objects.get(recipe=owned_recipe).tag_id  # pyright: ignore[reportAttributeAccessIssue]

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Recipe.objects.filter(pk=owned_recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not Step.objects.filter(recipe_id=owned_recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not RecipeIngredient.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        recipe_id=owned_recipe.pk
    ).exists()
    assert not RecipeTag.objects.filter(recipe_id=owned_recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    # Shared master data (the ingredient/tag rows themselves) is untouched.
    assert Ingredient.objects.filter(pk=ingredient_id).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert Tag.objects.filter(pk=tag_id).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_owner_can_create_recipe_in_own_cookbook(auth_client: APIClient, owned_cookbook: Cookbook):
    """Test that a user can file a new recipe into their own cookbook."""
    url = reverse("recipe-list")

    response = auth_client.post(
        url, {"title": "Filed Recipe", "cookbook": owned_cookbook.pk}, format="json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["cookbook"] == owned_cookbook.pk


def test_owner_can_create_recipe_in_cookbook_shared_with_them(
    auth_client: APIClient, cookbook_shared_with_regular_user: Cookbook
):
    """Test that a user can file a recipe into a cookbook shared with them."""
    url = reverse("recipe-list")

    response = auth_client.post(
        url,
        {"title": "Shared Cookbook Recipe", "cookbook": cookbook_shared_with_regular_user.pk},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["cookbook"] == cookbook_shared_with_regular_user.pk
