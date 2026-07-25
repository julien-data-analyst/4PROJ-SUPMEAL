import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User

pytestmark = pytest.mark.django_db

#############################################-
# Tests for unauthorized access to user data
#############################################-

def test_anonymous_user_cannot_list_users(api_client: APIClient):
    """Test that an anonymous user cannot list users and receives a 401 Unauthorized response."""
    url = reverse("user-list")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_anonymous_user_cannot_retrieve_a_user(api_client: APIClient, regular_user: User):
    """Test that an anonymous user cannot retrieve a user's details and receives a 401 Unauthorized response."""
    url = reverse("user-detail", kwargs={"pk": regular_user.pk})

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_non_staff_user_cannot_list_users(auth_client: APIClient):
    """Test that a non-staff user cannot list users and receives a 403 Forbidden response."""
    url = reverse("user-list")

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_non_staff_user_cannot_retrieve_another_user(auth_client: APIClient, other_user: User):
    """Test that a non-staff user cannot retrieve another user's details and receives a 403 Forbidden response."""
    url = reverse("user-detail", kwargs={"pk": other_user.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_non_staff_user_cannot_update_another_user(auth_client: APIClient, other_user: User):
    """Test that a non-staff user cannot update another user's details and receives a 403 Forbidden response."""
    url = reverse("user-detail", kwargs={"pk": other_user.pk})

    response = auth_client.patch(url, {"first_name": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    other_user.refresh_from_db()
    assert other_user.first_name != "Hacked"


def test_non_staff_user_cannot_delete_another_user(auth_client: APIClient, other_user: User):
    """Test that a non-staff user cannot delete another user's account and receives a 403 Forbidden response."""
    url = reverse("user-detail", kwargs={"pk": other_user.pk})

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert User.objects.filter(pk=other_user.pk).exists()
