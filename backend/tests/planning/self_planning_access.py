import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from planning.models import DEFAULT_PLANNING_ICON, Planning, RecipePlanning
from recipes.models import Recipe
from tests.planning.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

#######################################################-
# Tests for a planning owner's create/update/delete access
#######################################################-


def test_owner_can_create_planning_with_meals(
    auth_client: APIClient, regular_user: User, planning_payload: dict
):
    """Test that creating a planning also creates its scheduled meals."""
    url = reverse("planning-list")

    response = auth_client.post(url, planning_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["name"] == "Semaine du 27 juillet"
    assert response.data["creator"]["id"] == regular_user.pk
    assert len(response.data["meals"]) == 3

    planning = Planning.objects.get(pk=response.data["id"])  # pyright: ignore[reportAttributeAccessIssue]
    assert planning.creator_id == regular_user.pk
    assert RecipePlanning.objects.filter(planning=planning).count() == 3  # pyright: ignore[reportAttributeAccessIssue]


def test_owner_can_create_planning_without_optional_meals(auth_client: APIClient):
    """Test that meals are optional when creating a planning."""
    url = reverse("planning-list")

    response = auth_client.post(url, {"name": "Semaine vide"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["meals"] == []


def test_creating_a_planning_without_icon_gets_the_hardcoded_default(auth_client: APIClient):
    """Test that a planning created without an ``icon`` gets the hard-coded default one."""
    url = reverse("planning-list")

    response = auth_client.post(url, {"name": "Semaine vide"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["icon"] == DEFAULT_PLANNING_ICON


def test_creating_a_planning_with_a_custom_icon_uses_it(auth_client: APIClient):
    """Test that an explicit ``icon`` overrides the hard-coded default."""
    url = reverse("planning-list")
    custom_icon = "data:image/png;base64,iVBORw0KGgo="

    response = auth_client.post(url, {"name": "Semaine vide", "icon": custom_icon}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["icon"] == custom_icon


def test_creating_planning_rejects_disallowed_icon_type(auth_client: APIClient):
    """Test that a planning icon must be a PNG/JPEG/SVG data URI (see
    common.image_validation.validate_image_data_uri)."""
    url = reverse("planning-list")

    response = auth_client.post(
        url,
        {"name": "Mauvaise icone", "icon": "data:image/gif;base64,R0lGODlhAQABAAAAACw="},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Planning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        name="Mauvaise icone"
    ).exists()


def test_creating_a_planning_without_type_defaults_to_weekly(auth_client: APIClient):
    """Test that a planning created without a ``type`` defaults to "hebdomadaire"."""
    url = reverse("planning-list")

    response = auth_client.post(url, {"name": "Semaine vide"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["type"] == Planning.Type.WEEKLY


def test_owner_can_create_a_daily_planning_with_six_meals(
    auth_client: APIClient, regular_user: User
):
    """Test that a "journalier" planning can hold a full day of 6 meals (2 moments x 3
    courses)."""
    recipes = [Recipe.objects.create(title=f"Recette {i}", creator=regular_user) for i in range(6)]  # pyright: ignore[reportAttributeAccessIssue]
    url = reverse("planning-list")
    meals = [
        {"recipe": recipes[0].pk, "dayofweek": "lundi", "lunch": "midi", "type": "entree"},
        {"recipe": recipes[1].pk, "dayofweek": "lundi", "lunch": "midi", "type": "plat"},
        {"recipe": recipes[2].pk, "dayofweek": "lundi", "lunch": "midi", "type": "dessert"},
        {"recipe": recipes[3].pk, "dayofweek": "lundi", "lunch": "soir", "type": "entree"},
        {"recipe": recipes[4].pk, "dayofweek": "lundi", "lunch": "soir", "type": "plat"},
        {"recipe": recipes[5].pk, "dayofweek": "lundi", "lunch": "soir", "type": "dessert"},
    ]

    response = auth_client.post(
        url,
        {"name": "Journee complete", "type": Planning.Type.DAILY, "meals": meals},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["type"] == Planning.Type.DAILY
    assert len(response.data["meals"]) == 6


def test_daily_planning_rejects_meals_on_more_than_one_day(
    auth_client: APIClient, entree_recipe: Recipe, plat_recipe: Recipe
):
    """Test that a "journalier" planning can't schedule meals across several days."""
    url = reverse("planning-list")
    meals = [
        {"recipe": entree_recipe.pk, "dayofweek": "lundi", "lunch": "midi", "type": "entree"},
        {"recipe": plat_recipe.pk, "dayofweek": "mardi", "lunch": "midi", "type": "plat"},
    ]

    response = auth_client.post(
        url,
        {"name": "Journee invalide", "type": Planning.Type.DAILY, "meals": meals},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Planning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        name="Journee invalide"
    ).exists()


def test_creating_planning_rejects_invalid_type(auth_client: APIClient):
    """Test that ``type`` is restricted to "journalier"/"hebdomadaire"."""
    url = reverse("planning-list")

    response = auth_client.post(url, {"name": "Type invalide", "type": "mensuel"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Planning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        name="Type invalide"
    ).exists()


def test_owner_can_schedule_a_full_day_of_six_meals(auth_client: APIClient, regular_user: User):
    """Test that a single day can hold up to 6 recipes (2 moments x 3 courses)."""
    recipes = [Recipe.objects.create(title=f"Recette {i}", creator=regular_user) for i in range(6)]  # pyright: ignore[reportAttributeAccessIssue]
    url = reverse("planning-list")
    meals = [
        {"recipe": recipes[0].pk, "dayofweek": "lundi", "lunch": "midi", "type": "entree"},
        {"recipe": recipes[1].pk, "dayofweek": "lundi", "lunch": "midi", "type": "plat"},
        {"recipe": recipes[2].pk, "dayofweek": "lundi", "lunch": "midi", "type": "dessert"},
        {"recipe": recipes[3].pk, "dayofweek": "lundi", "lunch": "soir", "type": "entree"},
        {"recipe": recipes[4].pk, "dayofweek": "lundi", "lunch": "soir", "type": "plat"},
        {"recipe": recipes[5].pk, "dayofweek": "lundi", "lunch": "soir", "type": "dessert"},
    ]

    response = auth_client.post(url, {"name": "Journee complete", "meals": meals}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert len(response.data["meals"]) == 6


def test_owner_can_schedule_the_same_recipe_on_several_days(
    auth_client: APIClient, entree_recipe: Recipe
):
    """Test that the same recipe can be scheduled more than once in a planning."""
    url = reverse("planning-list")
    meals = [
        {"recipe": entree_recipe.pk, "dayofweek": "lundi", "lunch": "midi", "type": "entree"},
        {"recipe": entree_recipe.pk, "dayofweek": "mardi", "lunch": "soir", "type": "plat"},
    ]

    response = auth_client.post(url, {"name": "Recette repetee", "meals": meals}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert len(response.data["meals"]) == 2
    assert (
        RecipePlanning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            recipe=entree_recipe
        ).count()
        == 2
    )


def test_creating_planning_rejects_two_recipes_in_the_same_slot(
    auth_client: APIClient, entree_recipe: Recipe, plat_recipe: Recipe
):
    """Test that a single (day, meal moment, course) slot can't hold two recipes."""
    url = reverse("planning-list")
    meals = [
        {"recipe": entree_recipe.pk, "dayofweek": "lundi", "lunch": "midi", "type": "entree"},
        {"recipe": plat_recipe.pk, "dayofweek": "lundi", "lunch": "midi", "type": "entree"},
    ]

    response = auth_client.post(url, {"name": "Conflit", "meals": meals}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Planning.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_owner_can_partial_update_name_without_touching_meals(
    auth_client: APIClient, owned_planning: Planning
):
    """Test that a partial update omitting meals leaves the schedule untouched."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = auth_client.patch(url, {"name": "Renamed Planning"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["name"] == "Renamed Planning"
    assert len(response.data["meals"]) == 2


def test_owner_can_replace_meals_on_update(
    auth_client: APIClient, owned_planning: Planning, dessert_recipe: Recipe
):
    """Test that sending a new meals list replaces the old schedule."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = auth_client.patch(
        url,
        {
            "meals": [
                {
                    "recipe": dessert_recipe.pk,
                    "dayofweek": "dimanche",
                    "lunch": "soir",
                    "type": "dessert",
                }
            ]
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert len(response.data["meals"]) == 1
    assert response.data["meals"][0]["recipe"]["id"] == dessert_recipe.pk
    assert response.data["meals"][0]["dayofweek"] == "dimanche"


def test_owner_can_clear_meals_with_empty_list(auth_client: APIClient, owned_planning: Planning):
    """Test that sending an empty meals list removes all scheduled meals."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = auth_client.patch(url, {"meals": []}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["meals"] == []
    assert not RecipePlanning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        planning=owned_planning
    ).exists()


def test_owner_can_replace_planning_via_put_without_clearing_omitted_meals(
    auth_client: APIClient, owned_planning: Planning
):
    """Test that a full PUT omitting meals still leaves the schedule untouched."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = auth_client.put(url, {"name": "Fully Replaced"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["name"] == "Fully Replaced"
    assert len(response.data["meals"]) == 2


def test_owner_can_delete_own_planning(auth_client: APIClient, owned_planning: Planning):
    """Test that deleting a planning also removes its scheduled meals."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Planning.objects.filter(pk=owned_planning.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not RecipePlanning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        planning_id=owned_planning.pk
    ).exists()


def test_owner_can_create_planning_in_own_cookbook(
    auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test that a user can scope a new planning to their own cookbook."""
    url = reverse("planning-list")

    response = auth_client.post(
        url, {"name": "Planning classe", "cookbook": owned_cookbook.pk}, format="json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["cookbook"] == owned_cookbook.pk


def test_owner_can_create_planning_in_cookbook_shared_with_them(
    auth_client: APIClient, cookbook_shared_with_regular_user: Cookbook
):
    """Test that a user can scope a planning to a cookbook shared with them."""
    url = reverse("planning-list")

    response = auth_client.post(
        url,
        {"name": "Planning partage", "cookbook": cookbook_shared_with_regular_user.pk},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["cookbook"] == cookbook_shared_with_regular_user.pk


def test_owner_cannot_file_an_existing_personal_planning_into_a_cookbook(
    auth_client: APIClient, owned_planning: Planning, owned_cookbook: Cookbook
):
    """A planning's cookbook can only be chosen at creation - not assigned afterwards."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = auth_client.patch(url, {"cookbook": owned_cookbook.pk}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    owned_planning.refresh_from_db()
    assert owned_planning.cookbook_id is None  # pyright: ignore[reportAttributeAccessIssue]


def test_owner_cannot_move_a_planning_from_one_cookbook_to_another(
    auth_client: APIClient, owned_cookbook: Cookbook, cookbook_shared_with_regular_user: Cookbook
):
    """A planning already filed in cookbook A cannot be moved directly to cookbook B."""
    create_url = reverse("planning-list")
    created = auth_client.post(
        create_url, {"name": "Semaine 1", "cookbook": owned_cookbook.pk}, format="json"
    )
    planning_id = created.data["id"]  # pyright: ignore[reportOptionalSubscript]

    url = reverse("planning-detail", kwargs={"pk": planning_id})
    response = auth_client.patch(
        url, {"cookbook": cookbook_shared_with_regular_user.pk}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    planning = Planning.objects.get(pk=planning_id)  # pyright: ignore[reportAttributeAccessIssue]
    assert planning.cookbook_id == owned_cookbook.pk


def test_owner_can_remove_a_planning_from_its_cookbook(
    auth_client: APIClient, owned_cookbook: Cookbook
):
    """Clearing a planning's cookbook back to personal (-> None) stays allowed."""
    create_url = reverse("planning-list")
    created = auth_client.post(
        create_url, {"name": "Semaine 1", "cookbook": owned_cookbook.pk}, format="json"
    )
    planning_id = created.data["id"]  # pyright: ignore[reportOptionalSubscript]

    url = reverse("planning-detail", kwargs={"pk": planning_id})
    response = auth_client.patch(url, {"cookbook": None}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["cookbook"] is None  # pyright: ignore[reportOptionalSubscript]
