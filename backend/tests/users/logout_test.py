import pytest
from django.urls import reverse
from rest_framework import status

from tests.users.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

#############################################-
# Tests for the logout route
#############################################-


def _login(client: APIClient, user: User, password: str) -> dict:
    response = client.post(
        reverse("user-login"), {"email": user.email, "password": password}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    return response.data


def _bearer(client: APIClient, access: str) -> APIClient:
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


def test_logout_requires_authentication(api_client: APIClient):
    response = api_client.post(reverse("user-logout"), {"refresh": "irrelevant"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_requires_refresh_field(
    api_client: APIClient, regular_user: User, test_password: str
):
    tokens = _login(api_client, regular_user, test_password)
    client = _bearer(api_client, tokens["access"])

    response = client.post(reverse("user-logout"), {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_logout_rejects_get_requests(api_client: APIClient, regular_user: User, test_password: str):
    tokens = _login(api_client, regular_user, test_password)
    client = _bearer(api_client, tokens["access"])

    response = client.get(reverse("user-logout"))

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_logout_rejects_malformed_refresh_token(
    api_client: APIClient, regular_user: User, test_password: str
):
    tokens = _login(api_client, regular_user, test_password)
    client = _bearer(api_client, tokens["access"])

    response = client.post(reverse("user-logout"), {"refresh": "not-a-real-token"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_logout_rejects_refresh_token_belonging_to_another_user(
    regular_user: User, other_user: User, test_password: str
):
    victim_tokens = _login(APIClient(), regular_user, test_password)
    attacker_client = APIClient()
    attacker_tokens = _login(attacker_client, other_user, test_password)
    _bearer(attacker_client, attacker_tokens["access"])

    response = attacker_client.post(
        reverse("user-logout"), {"refresh": victim_tokens["refresh"]}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # The victim's refresh token must still be usable, since it wasn't blacklisted.
    refresh_response = APIClient().post(
        reverse("token-refresh"), {"refresh": victim_tokens["refresh"]}, format="json"
    )
    assert refresh_response.status_code == status.HTTP_200_OK


def test_logout_blacklists_refresh_token(
    api_client: APIClient, regular_user: User, test_password: str
):
    tokens = _login(api_client, regular_user, test_password)
    client = _bearer(api_client, tokens["access"])

    response = client.post(reverse("user-logout"), {"refresh": tokens["refresh"]}, format="json")
    assert response.status_code == status.HTTP_200_OK

    refresh_response = APIClient().post(
        reverse("token-refresh"), {"refresh": tokens["refresh"]}, format="json"
    )
    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_blacklists_current_access_token(
    api_client: APIClient, regular_user: User, test_password: str
):
    tokens = _login(api_client, regular_user, test_password)
    client = _bearer(api_client, tokens["access"])

    logout_response = client.post(
        reverse("user-logout"), {"refresh": tokens["refresh"]}, format="json"
    )
    assert logout_response.status_code == status.HTTP_200_OK

    me_response = client.get(reverse("user-me"))

    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_with_already_blacklisted_refresh_token_fails(
    api_client: APIClient, regular_user: User, test_password: str
):
    tokens = _login(api_client, regular_user, test_password)
    first_client = _bearer(api_client, tokens["access"])
    first_logout = first_client.post(
        reverse("user-logout"), {"refresh": tokens["refresh"]}, format="json"
    )
    assert first_logout.status_code == status.HTTP_200_OK

    new_tokens = _login(APIClient(), regular_user, test_password)
    second_client = _bearer(APIClient(), new_tokens["access"])

    second_logout = second_client.post(
        reverse("user-logout"), {"refresh": tokens["refresh"]}, format="json"
    )

    assert second_logout.status_code == status.HTTP_400_BAD_REQUEST
