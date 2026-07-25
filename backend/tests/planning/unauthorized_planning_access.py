import pytest
from django.urls import reverse
from rest_framework import status

from planning.models import Planning, RecipePlanning
from tests.planning.conftest import APIClient

pytestmark = pytest.mark.django_db

##########################################################-
# Tests for unauthorized access to another user's plannings
##########################################################-


def test_anonymous_user_cannot_create_planning(api_client: APIClient, planning_payload: dict):
    """Test that an anonymous user cannot create a planning and receives a 401 response."""
    url = reverse("planning-list")

    response = api_client.post(url, planning_payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not Planning.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_anonymous_user_cannot_update_a_planning(api_client: APIClient, owned_planning: Planning):
    """Test that an anonymous user cannot update a planning and receives a 401 response."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = api_client.patch(url, {"name": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    owned_planning.refresh_from_db()
    assert owned_planning.name != "Hacked"


def test_anonymous_user_cannot_delete_a_planning(api_client: APIClient, owned_planning: Planning):
    """Test that an anonymous user cannot delete a planning and receives a 401 response."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Planning.objects.filter(pk=owned_planning.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_other_user_cannot_update_someone_elses_planning(
    other_auth_client: APIClient, owned_planning: Planning
):
    """Test that a non-owner cannot partially update another user's planning (403)."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = other_auth_client.patch(url, {"name": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    owned_planning.refresh_from_db()
    assert owned_planning.name != "Hacked"


def test_other_user_cannot_replace_someone_elses_planning_via_put(
    other_auth_client: APIClient, owned_planning: Planning
):
    """Test that a non-owner cannot fully replace another user's planning (403)."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = other_auth_client.put(url, {"name": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    owned_planning.refresh_from_db()
    assert owned_planning.name != "Hacked"


def test_other_user_cannot_inject_meals_via_update(
    other_auth_client: APIClient, owned_planning: Planning, dessert_recipe
):
    """Test that a denied update can't sneak in a new schedule for another user's planning."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})
    original_count = RecipePlanning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        planning=owned_planning
    ).count()

    payload = {
        "meals": [
            {
                "recipe": dessert_recipe.pk,
                "dayofweek": "dimanche",
                "lunch": "soir",
                "type": "dessert",
            }
        ]
    }
    response = other_auth_client.patch(url, payload, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        RecipePlanning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            planning=owned_planning
        ).count()
        == original_count
    )


def test_other_user_cannot_delete_someone_elses_planning(
    other_auth_client: APIClient, owned_planning: Planning
):
    """Test that a non-owner cannot delete another user's planning (403)."""
    url = reverse("planning-detail", kwargs={"pk": owned_planning.pk})

    response = other_auth_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Planning.objects.filter(pk=owned_planning.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert RecipePlanning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        planning=owned_planning
    ).exists()


def test_user_cannot_create_planning_in_someone_elses_private_cookbook(
    auth_client: APIClient, other_users_cookbook
):
    """Test that scoping a planning to an inaccessible cookbook is rejected (400)."""
    url = reverse("planning-list")

    response = auth_client.post(
        url,
        {"name": "Intrusion", "cookbook": other_users_cookbook.pk},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Planning.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]
