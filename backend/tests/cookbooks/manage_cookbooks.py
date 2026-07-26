import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from planning.models import Planning
from recipes.models import Recipe
from tests.cookbooks.conftest import APIClient

pytestmark = pytest.mark.django_db

#################################################################-
# Tests for creating/renaming/deleting a cookbook and its contents
#################################################################-


def test_owner_can_create_cookbook(auth_client: APIClient, regular_user):
    """Test that creating a cookbook sets the caller as its creator/admin."""
    url = reverse("cookbook-list")

    response = auth_client.post(url, {"name": "Mon carnet"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["name"] == "Mon carnet"
    assert response.data["creator"]["id"] == regular_user.pk
    assert response.data["shared_with"] == []


def test_owner_can_rename_own_cookbook(auth_client: APIClient, owned_cookbook: Cookbook):
    """Test that the cookbook's admin (its creator) can rename it."""
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.patch(url, {"name": "Nouveau nom"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    owned_cookbook.refresh_from_db()
    assert owned_cookbook.name == "Nouveau nom"


def test_owner_can_delete_own_cookbook(auth_client: APIClient, owned_cookbook: Cookbook):
    """Test that the cookbook's admin can delete it."""
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Cookbook.objects.filter(pk=owned_cookbook.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_anonymous_user_cannot_create_cookbook(api_client: APIClient):
    """Test that an anonymous user cannot create a cookbook and receives a 401 response."""
    url = reverse("cookbook-list")

    response = api_client.post(url, {"name": "Intrus"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not Cookbook.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_stranger_cannot_see_or_rename_someone_elses_cookbook(
    other_auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test that a user with no relation to the cookbook can't rename it (404 - not visible)."""
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = other_auth_client.patch(url, {"name": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    owned_cookbook.refresh_from_db()
    assert owned_cookbook.name != "Hacked"


def test_stranger_cannot_delete_someone_elses_cookbook(
    other_auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test that a user with no relation to the cookbook can't delete it (404)."""
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = other_auth_client.delete(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Cookbook.objects.filter(pk=owned_cookbook.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_shared_editor_cannot_rename_cookbook(
    auth_client: APIClient, cookbook_shared_as_editor: Cookbook
):
    """Test that a non-admin member (e.g. editor) can see the cookbook but not rename it (403)."""
    url = reverse("cookbook-detail", kwargs={"pk": cookbook_shared_as_editor.pk})

    response = auth_client.patch(url, {"name": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_owner_can_create_and_delete_recipe_in_own_cookbook(
    auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test the owner's happy path: filing a recipe into their own cookbook, then deleting it."""
    create_url = reverse("recipe-list")

    create_response = auth_client.post(
        create_url, {"title": "Recette du carnet", "cookbook": owned_cookbook.pk}, format="json"
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.data is not None
    recipe_id = create_response.data["id"]
    delete_response = auth_client.delete(reverse("recipe-detail", kwargs={"pk": recipe_id}))

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Recipe.objects.filter(pk=recipe_id).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_owner_can_create_and_delete_planning_in_own_cookbook(
    auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test the owner's happy path: filing a planning into their own cookbook, then deleting it."""
    create_url = reverse("planning-list")

    create_response = auth_client.post(
        create_url, {"name": "Semaine 1", "cookbook": owned_cookbook.pk}, format="json"
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.data is not None
    planning_id = create_response.data["id"]
    delete_response = auth_client.delete(reverse("planning-detail", kwargs={"pk": planning_id}))

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Planning.objects.filter(pk=planning_id).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_cookbook_detail_lists_its_recipes_and_plannings(
    auth_client: APIClient, owned_cookbook: Cookbook, regular_user
):
    """Test that a cookbook's detail response includes the recipes/plannings filed into it."""
    recipe = Recipe(title="Recette du carnet", creator=regular_user, cookbook=owned_cookbook)
    recipe.save()
    planning = Planning(name="Semaine 1", creator=regular_user, cookbook=owned_cookbook)
    planning.save()
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert [r["id"] for r in response.data["recipes"]] == [recipe.pk]
    assert response.data["recipes"][0]["title"] == "Recette du carnet"
    assert [p["id"] for p in response.data["plannings"]] == [planning.pk]
    assert response.data["plannings"][0]["name"] == "Semaine 1"


##########################################-
# shared_with_me: cookbooks shared with the caller vs. their own
##########################################-


def test_shared_with_me_filter_true_returns_only_cookbooks_shared_with_caller(
    auth_client: APIClient, owned_cookbook: Cookbook, cookbook_shared_as_reader: Cookbook
):
    """Test that ``?shared_with_me=true`` only returns cookbooks shared with the caller,
    not the ones they created themselves.
    """
    url = reverse("cookbook-list")

    response = auth_client.get(url, {"shared_with_me": "true"})

    assert response.data is not None
    names = [item["name"] for item in response.data["results"]]
    assert names == [cookbook_shared_as_reader.name]


def test_shared_with_me_filter_false_returns_only_the_callers_own_cookbooks(
    auth_client: APIClient, owned_cookbook: Cookbook, cookbook_shared_as_reader: Cookbook
):
    """Test that ``?shared_with_me=false`` excludes cookbooks shared with the caller,
    keeping only the ones they created themselves.
    """
    url = reverse("cookbook-list")

    response = auth_client.get(url, {"shared_with_me": "false"})

    assert response.data is not None
    names = [item["name"] for item in response.data["results"]]
    assert names == [owned_cookbook.name]
