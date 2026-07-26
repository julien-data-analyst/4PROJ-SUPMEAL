from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from recipes.models import Ingredient, Recipe, Tag
from tests.import_export.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

#########################################-
# Tests for GET /api/recipes/{id}/export/
#########################################-


def test_export_detail_returns_portable_shape_without_id_creator_or_cookbook(
    auth_client: APIClient, owned_recipe: Recipe
):
    url = reverse("recipe-export-detail", kwargs={"pk": owned_recipe.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["title"] == "Existing Recipe"
    assert "id" not in response.data
    assert "creator" not in response.data
    assert "cookbook" not in response.data
    assert response.data["tags"] == [{"name": "Plat", "type": "repas", "description": None}]
    assert response.data["ingredients"][0]["name"] == "Sel"
    assert response.data["ingredients"][0]["quantity"] == Decimal("5.00")
    assert response.data["steps"][0]["description"] == "Cuire a feu doux"
    assert "id" not in response.data["steps"][0]
    expected_disposition = f'attachment; filename="recipe_{owned_recipe.pk}.json"'
    assert response["Content-Disposition"] == expected_disposition


def test_export_detail_404_for_recipe_in_a_cookbook_not_shared_with_caller(
    auth_client: APIClient, other_users_private_recipe: Recipe
):
    url = reverse("recipe-export-detail", kwargs={"pk": other_users_private_recipe.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


#######################################-
# Tests for GET /api/recipes/export/
#######################################-


def test_export_list_only_returns_callers_personal_recipes(
    auth_client: APIClient, owned_recipe: Recipe, other_users_private_recipe: Recipe
):
    url = reverse("recipe-export-list")

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert len(response.data) == 1
    assert response.data[0]["title"] == "Existing Recipe"


def test_export_list_excludes_callers_recipes_filed_into_a_cookbook(
    auth_client: APIClient, owned_recipe: Recipe, owned_cookbook_with_recipe_and_planning
):
    url = reverse("recipe-export-list")

    response = auth_client.get(url)

    titles = [item["title"] for item in response.data]  # pyright: ignore[reportOptionalIterable]
    assert titles == ["Existing Recipe"]


#######################################-
# Tests for POST /api/recipes/import/
#######################################-


def test_import_single_recipe_object_creates_a_personal_recipe(
    auth_client: APIClient, regular_user: User, recipe_export_payload: dict
):
    url = reverse("recipe-import-data")

    response = auth_client.post(url, recipe_export_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert len(response.data) == 1
    created = response.data[0]
    assert created["title"] == "Crepes"
    assert created["cookbook"] is None
    assert created["creator"]["id"] == regular_user.pk
    assert len(created["ingredients"]) == 1
    assert len(created["tags"]) == 1
    assert len(created["steps"]) == 1

    recipe = Recipe.objects.get(pk=created["id"])  # pyright: ignore[reportAttributeAccessIssue]
    assert recipe.cookbook_id is None
    assert recipe.creator_id == regular_user.pk


def test_import_array_of_recipes_creates_all_of_them(
    auth_client: APIClient, recipe_export_payload: dict
):
    url = reverse("recipe-import-data")
    second = {**recipe_export_payload, "title": "Gaufres"}

    response = auth_client.post(url, [recipe_export_payload, second], format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert len(response.data) == 2
    assert {item["title"] for item in response.data} == {"Crepes", "Gaufres"}
    assert Recipe.objects.count() == 2  # pyright: ignore[reportAttributeAccessIssue]


def test_import_reuses_existing_ingredient_and_tag_by_name_case_insensitively(
    auth_client: APIClient, recipe_export_payload: dict
):
    Ingredient(name="farine").save()  # pyright: ignore[reportAttributeAccessIssue]
    Tag(name="dessert", type="repas").save()  # pyright: ignore[reportAttributeAccessIssue]
    url = reverse("recipe-import-data")

    response = auth_client.post(url, recipe_export_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert Ingredient.objects.count() == 1  # pyright: ignore[reportAttributeAccessIssue]
    assert Tag.objects.count() == 1  # pyright: ignore[reportAttributeAccessIssue]


def test_import_ignores_a_cookbook_key_if_present_in_the_payload(
    auth_client: APIClient, owned_cookbook_with_recipe_and_planning, recipe_export_payload: dict
):
    recipe_export_payload["cookbook"] = owned_cookbook_with_recipe_and_planning.pk
    url = reverse("recipe-import-data")

    response = auth_client.post(url, recipe_export_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data[0]["cookbook"] is None  # pyright: ignore[reportOptionalSubscript]


def test_import_rejects_invalid_payload_and_creates_nothing(auth_client: APIClient):
    url = reverse("recipe-import-data")

    response = auth_client.post(url, {"ingredients": []}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Recipe.objects.count() == 0  # pyright: ignore[reportAttributeAccessIssue]


def test_import_of_a_partially_invalid_list_creates_nothing(
    auth_client: APIClient, recipe_export_payload: dict
):
    """All-or-nothing: one bad item in the array must roll back the whole batch."""
    url = reverse("recipe-import-data")

    response = auth_client.post(
        url, [recipe_export_payload, {"title": ""}], format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Recipe.objects.count() == 0  # pyright: ignore[reportAttributeAccessIssue]


def test_export_then_reimport_round_trips_as_a_personal_recipe_for_the_importer(
    auth_client: APIClient, other_user_client: APIClient, other_user: User, owned_recipe: Recipe
):
    export_url = reverse("recipe-export-detail", kwargs={"pk": owned_recipe.pk})
    exported = auth_client.get(export_url).data

    import_url = reverse("recipe-import-data")
    response = other_user_client.post(import_url, exported, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    created = response.data[0]  # pyright: ignore[reportOptionalSubscript]
    assert created["id"] != owned_recipe.pk
    assert created["title"] == owned_recipe.title
    assert created["creator"]["id"] == other_user.pk
    assert created["cookbook"] is None
    assert Recipe.objects.filter(pk=owned_recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
