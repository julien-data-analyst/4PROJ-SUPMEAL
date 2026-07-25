import pytest
from django.urls import reverse
from rest_framework import status

from recipes.models import Recipe, RecipeIngredient, RecipeTag, Step
from tests.recipes.conftest import APIClient

pytestmark = pytest.mark.django_db

########################################################-
# Tests for unauthorized access to another user's recipes
########################################################-


def test_anonymous_user_cannot_create_recipe(api_client: APIClient, recipe_payload: dict):
    """Test that an anonymous user cannot create a recipe and receives a 401 response."""
    url = reverse("recipe-list")

    response = api_client.post(url, recipe_payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not Recipe.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_anonymous_user_cannot_update_a_recipe(api_client: APIClient, owned_recipe: Recipe):
    """Test that an anonymous user cannot update a recipe and receives a 401 response."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})

    response = api_client.patch(url, {"title": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    owned_recipe.refresh_from_db()
    assert owned_recipe.title != "Hacked"


def test_anonymous_user_cannot_delete_a_recipe(api_client: APIClient, owned_recipe: Recipe):
    """Test that an anonymous user cannot delete a recipe and receives a 401 response."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Recipe.objects.filter(pk=owned_recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_other_user_cannot_update_someone_elses_recipe(
    other_auth_client: APIClient, owned_recipe: Recipe
):
    """Test that a non-owner cannot partially update another user's recipe (403)."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})

    response = other_auth_client.patch(url, {"title": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    owned_recipe.refresh_from_db()
    assert owned_recipe.title != "Hacked"


def test_other_user_cannot_replace_someone_elses_recipe_via_put(
    other_auth_client: APIClient, owned_recipe: Recipe
):
    """Test that a non-owner cannot fully replace another user's recipe (403)."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})

    response = other_auth_client.put(url, {"title": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    owned_recipe.refresh_from_db()
    assert owned_recipe.title != "Hacked"


def test_other_user_cannot_inject_ingredients_via_update(
    other_auth_client: APIClient, owned_recipe: Recipe
):
    """Test that a denied update can't sneak in new ingredients for another user's recipe."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})
    original_count = RecipeIngredient.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=owned_recipe
    ).count()

    payload = {
        "ingredients": [{"name": "Intrus", "quantity": "1.00", "unity": "g", "person_numbers": 1}]
    }
    response = other_auth_client.patch(url, payload, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        RecipeIngredient.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            recipe=owned_recipe
        ).count()
        == original_count
    )


def test_other_user_cannot_delete_someone_elses_recipe(
    other_auth_client: APIClient, owned_recipe: Recipe
):
    """Test that a non-owner cannot delete another user's recipe (403)."""
    url = reverse("recipe-detail", kwargs={"pk": owned_recipe.pk})

    response = other_auth_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Recipe.objects.filter(pk=owned_recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert Step.objects.filter(recipe=owned_recipe).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert RecipeTag.objects.filter(recipe=owned_recipe).exists()  # pyright: ignore[reportAttributeAccessIssue]
