import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User

pytestmark = pytest.mark.django_db

#############################################-
# Tests for staff users accessing other users' data (Staff represent the Admin/support Roles for managing users accounts in case of issues)
#############################################-

def test_staff_can_list_users(staff_client: APIClient, staff_user: User, other_user: User):
    """Test that a staff user can list all users and receives a 200 OK response."""
    url = reverse("user-list")

    response = staff_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    returned_ids = {user["id"] for user in response.data}
    assert {staff_user.id, other_user.id} <= returned_ids


def test_staff_can_retrieve_another_user(staff_client: APIClient, other_user: User):
    """Test that a staff user can retrieve another user's details and receives a 200 OK response."""
    url = reverse("user-detail", kwargs={"pk": other_user.pk})

    response = staff_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == other_user.id


def test_staff_can_update_another_user(staff_client: APIClient, other_user: User):
    """Test that a staff user can update another user's details and receives a 200 OK response."""
    url = reverse("user-detail", kwargs={"pk": other_user.pk})

    response = staff_client.patch(url, {"first_name": "Moderated"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    other_user.refresh_from_db()
    assert other_user.first_name == "Moderated"


def test_staff_can_delete_another_user(staff_client: APIClient, other_user: User):
    """Test that a staff user can delete another user's account and receives a 204 No Content response."""
    url = reverse("user-detail", kwargs={"pk": other_user.pk})

    response = staff_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(pk=other_user.pk).exists()


def test_staff_can_still_access_own_profile_via_me(staff_client: APIClient, staff_user: User):
    """Test that a staff user can still access their own profile via the /me endpoint."""
    url = reverse("user-me")

    response = staff_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == staff_user.id
