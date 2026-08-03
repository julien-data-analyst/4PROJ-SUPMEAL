import pytest
from django.urls import reverse
from rest_framework import status

from tests.users.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

#############################################-
# Tests for the self-service change-password route
#############################################-


def test_change_password_requires_authentication(api_client: APIClient):
    url = reverse("change-password")

    response = api_client.post(
        url,
        {"current_password": "irrelevant", "new_password": "N3wC0mplexPassw0rd!"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_password_with_correct_current_password_succeeds(
    auth_client: APIClient, regular_user: User, test_password: str
):
    url = reverse("change-password")

    response = auth_client.post(
        url,
        {"current_password": test_password, "new_password": "N3wC0mplexPassw0rd!"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    regular_user.refresh_from_db()
    assert regular_user.check_password("N3wC0mplexPassw0rd!")
    assert not regular_user.check_password(test_password)


def test_change_password_with_wrong_current_password_is_rejected(
    auth_client: APIClient, regular_user: User, test_password: str
):
    url = reverse("change-password")

    response = auth_client.post(
        url,
        {"current_password": "totally-wrong-password", "new_password": "N3wC0mplexPassw0rd!"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    regular_user.refresh_from_db()
    assert regular_user.check_password(test_password)


def test_change_password_rejects_weak_new_password(
    auth_client: APIClient, regular_user: User, test_password: str
):
    url = reverse("change-password")

    response = auth_client.post(
        url, {"current_password": test_password, "new_password": "12345678"}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    regular_user.refresh_from_db()
    assert regular_user.check_password(test_password)


def test_change_password_rejects_get_requests(auth_client: APIClient):
    url = reverse("change-password")

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_oauth_user_cannot_change_password(api_client: APIClient, oauth_user: User):
    api_client.force_authenticate(user=oauth_user)
    url = reverse("change-password")

    response = api_client.post(
        url,
        {"current_password": "whatever-it-is", "new_password": "N3wC0mplexPassw0rd!"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
