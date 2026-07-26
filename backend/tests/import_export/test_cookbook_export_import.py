import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from planning.models import Planning, RecipePlanning
from recipes.models import Recipe
from tests.import_export.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

###########################################-
# Tests for GET /api/cookbooks/{id}/export/
###########################################-


def test_export_detail_returns_recipes_with_link_id_and_plannings_referencing_it(
    auth_client: APIClient, owned_cookbook_with_recipe_and_planning: Cookbook
):
    cookbook = owned_cookbook_with_recipe_and_planning
    url = reverse("cookbook-export-detail", kwargs={"pk": cookbook.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data["name"] == "Mon carnet"
    assert "shared_with" not in data
    assert len(data["recipes"]) == 1
    recipe_data = data["recipes"][0]
    assert recipe_data["title"] == "Crepes"
    assert isinstance(recipe_data["id"], int)
    assert len(data["plannings"]) == 1
    meal = data["plannings"][0]["meals"][0]
    assert meal["recipe_id"] == recipe_data["id"]
    assert meal == {
        "recipe_id": recipe_data["id"],
        "type": "plat",
        "lunch": "midi",
        "dayofweek": "lundi",
    }
    assert (
        response["Content-Disposition"] == f'attachment; filename="cookbook_{cookbook.pk}.json"'
    )


def test_export_detail_drops_meals_scheduling_a_recipe_outside_the_cookbook(
    auth_client: APIClient, owned_cookbook_with_recipe_and_planning: Cookbook, owned_recipe: Recipe
):
    cookbook = owned_cookbook_with_recipe_and_planning
    planning = cookbook.plannings.first()  # pyright: ignore[reportAttributeAccessIssue]
    RecipePlanning(
        planning=planning, recipe=owned_recipe, type="entree", lunch="soir", dayofweek="mardi"
    ).save()

    url = reverse("cookbook-export-detail", kwargs={"pk": cookbook.pk})
    response = auth_client.get(url)

    meals = response.data["plannings"][0]["meals"]  # pyright: ignore[reportOptionalSubscript]
    assert len(meals) == 1
    assert meals[0]["lunch"] == "midi"


def test_export_detail_accessible_to_a_user_shared_at_reader_role(
    auth_client: APIClient, cookbook_shared_as_reader_with_regular_user: Cookbook
):
    url = reverse(
        "cookbook-export-detail", kwargs={"pk": cookbook_shared_as_reader_with_regular_user.pk}
    )

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK


def test_export_detail_404_for_a_cookbook_not_shared_with_caller(
    auth_client: APIClient, other_user: User
):
    other_cookbook = Cookbook(name="Carnet prive", creator=other_user)
    other_cookbook.save()
    url = reverse("cookbook-export-detail", kwargs={"pk": other_cookbook.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


#########################################-
# Tests for GET /api/cookbooks/export/
#########################################-


def test_export_list_only_returns_cookbooks_created_by_caller(
    auth_client: APIClient,
    owned_cookbook_with_recipe_and_planning: Cookbook,
    cookbook_shared_with_regular_user: Cookbook,
):
    """Cookbooks merely shared with the caller (not created by them) are excluded."""
    url = reverse("cookbook-export-list")

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    names = [item["name"] for item in response.data]  # pyright: ignore[reportOptionalIterable]
    assert names == ["Mon carnet"]


#########################################-
# Tests for POST /api/cookbooks/import/
#########################################-


def test_import_single_cookbook_creates_cookbook_recipe_and_planning(
    auth_client: APIClient, regular_user: User, cookbook_export_payload: dict
):
    url = reverse("cookbook-import-data")

    response = auth_client.post(url, cookbook_export_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.data) == 1  # pyright: ignore[reportArgumentType]
    created = response.data[0]  # pyright: ignore[reportOptionalSubscript]
    assert created["name"] == "Recettes de famille"
    assert created["creator"]["id"] == regular_user.pk
    assert len(created["recipes"]) == 1
    assert len(created["plannings"]) == 1

    cookbook = Cookbook.objects.get(pk=created["id"])  # pyright: ignore[reportAttributeAccessIssue]
    recipe = cookbook.recipes.first()  # pyright: ignore[reportAttributeAccessIssue]
    planning = cookbook.plannings.first()  # pyright: ignore[reportAttributeAccessIssue]
    assert recipe is not None and recipe.title == "Crepes"
    assert recipe.creator_id == regular_user.pk
    meal = planning.recipe_plannings.first()  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    assert meal.recipe_id == recipe.pk


def test_import_array_of_cookbooks_creates_all_of_them(
    auth_client: APIClient, cookbook_export_payload: dict
):
    url = reverse("cookbook-import-data")
    second = {**cookbook_export_payload, "name": "Deuxieme carnet"}

    response = auth_client.post(url, [cookbook_export_payload, second], format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert Cookbook.objects.count() == 2  # pyright: ignore[reportAttributeAccessIssue]
    assert Recipe.objects.count() == 2  # pyright: ignore[reportAttributeAccessIssue]


def test_import_rejects_a_meal_recipe_id_not_present_in_recipes(
    auth_client: APIClient, cookbook_export_payload: dict
):
    cookbook_export_payload["plannings"][0]["meals"][0]["recipe_id"] = 999
    url = reverse("cookbook-import-data")

    response = auth_client.post(url, cookbook_export_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Cookbook.objects.count() == 0  # pyright: ignore[reportAttributeAccessIssue]
    assert Planning.objects.count() == 0  # pyright: ignore[reportAttributeAccessIssue]


def test_import_rejects_duplicate_meal_slot_in_the_same_planning(
    auth_client: APIClient, cookbook_export_payload: dict
):
    duplicate_meal = dict(cookbook_export_payload["plannings"][0]["meals"][0])
    cookbook_export_payload["plannings"][0]["meals"].append(duplicate_meal)
    url = reverse("cookbook-import-data")

    response = auth_client.post(url, cookbook_export_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Cookbook.objects.count() == 0  # pyright: ignore[reportAttributeAccessIssue]


def test_import_does_not_create_any_cookbook_members(
    auth_client: APIClient, cookbook_export_payload: dict
):
    url = reverse("cookbook-import-data")

    response = auth_client.post(url, cookbook_export_payload, format="json")

    assert response.data[0]["shared_with"] == []  # pyright: ignore[reportOptionalSubscript]


def test_export_then_reimport_cookbook_round_trips_for_the_importer(
    auth_client: APIClient,
    other_user_client: APIClient,
    other_user: User,
    owned_cookbook_with_recipe_and_planning: Cookbook,
):
    export_url = reverse(
        "cookbook-export-detail", kwargs={"pk": owned_cookbook_with_recipe_and_planning.pk}
    )
    exported = auth_client.get(export_url).data

    import_url = reverse("cookbook-import-data")
    response = other_user_client.post(import_url, exported, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    created = response.data[0]  # pyright: ignore[reportOptionalSubscript]
    assert created["id"] != owned_cookbook_with_recipe_and_planning.pk
    assert created["creator"]["id"] == other_user.pk
    new_recipe_id = created["recipes"][0]["id"]
    assert created["plannings"][0]["meals"][0]["recipe"]["id"] == new_recipe_id
    assert Cookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        pk=owned_cookbook_with_recipe_and_planning.pk
    ).exists()
