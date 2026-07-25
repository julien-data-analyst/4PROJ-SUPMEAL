from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status

from tests.users.conftest import APIClient
from users.models import OAuthUser, User
from users.oauth_microsoft import GRAPH_ME_URL, GRAPH_PHOTO_URL

pytestmark = pytest.mark.django_db

#############################################-
# Tests for Microsoft OAuth login/registration
#############################################-

MICROSOFT_PROFILE = {
    "mail": "jane.doe@contoso.com",
    "userPrincipalName": "jane.doe@contoso.com",
    "givenName": "Jane",
    "surname": "Doe",
}


def _mock_response(*, ok: bool = True, status_code: int = 200, json_data=None, text: str = ""):
    response = MagicMock()
    response.ok = ok
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = text
    return response


def _mock_graph_get(*, has_photo: bool):
    def _get(url: str, *args, **kwargs):
        if url == GRAPH_ME_URL:
            return _mock_response(json_data=MICROSOFT_PROFILE)
        if url == GRAPH_PHOTO_URL:
            return _mock_response(ok=has_photo, status_code=200 if has_photo else 404)
        raise AssertionError(f"Unexpected URL requested: {url}")

    return _get


def _mock_confidential_client(*, access_token: str | None = "fake-access-token"):
    client = MagicMock()
    if access_token is None:
        client.acquire_token_by_authorization_code.return_value = {
            "error": "invalid_grant",
            "error_description": "AADSTS70008: The provided authorization code is expired.",
        }
    else:
        client.acquire_token_by_authorization_code.return_value = {
            "access_token": access_token,
        }
    return client


def test_microsoft_oauth_creates_new_user_with_profile_fields(api_client: APIClient):
    """A first-time Microsoft login creates a User + a linked OAuthUser("microsoft")."""
    url = reverse("oauth-microsoft")

    with (
        patch(
            "users.oauth_microsoft._confidential_client",
            return_value=_mock_confidential_client(),
        ),
        patch("users.oauth_microsoft.requests.get", side_effect=_mock_graph_get(has_photo=True)),
    ):
        response = api_client.post(url, {"code": "auth-code"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert "access" in response.data
    assert "refresh" in response.data

    user = User.objects.get(email="jane.doe@contoso.com")
    assert user.username == "jane.doe"
    assert user.first_name == "Jane"
    assert user.last_name == "Doe"
    assert user.profile_icon == GRAPH_PHOTO_URL
    assert not user.has_usable_password()

    oauth_account = OAuthUser.objects.get(  # pyright: ignore[reportAttributeAccessIssue]
        user=user, provider="microsoft"
    )
    assert oauth_account.domain == "contoso.com"
    assert oauth_account.profile_icon == GRAPH_PHOTO_URL


def test_microsoft_oauth_without_photo_leaves_profile_icon_empty(api_client: APIClient):
    url = reverse("oauth-microsoft")

    with (
        patch(
            "users.oauth_microsoft._confidential_client",
            return_value=_mock_confidential_client(),
        ),
        patch("users.oauth_microsoft.requests.get", side_effect=_mock_graph_get(has_photo=False)),
    ):
        response = api_client.post(url, {"code": "auth-code"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    user = User.objects.get(email="jane.doe@contoso.com")
    assert user.profile_icon == ""
    oauth_account = OAuthUser.objects.get(  # pyright: ignore[reportAttributeAccessIssue]
        user=user, provider="microsoft"
    )
    assert oauth_account.profile_icon == ""


def test_microsoft_oauth_links_to_existing_user_by_email(api_client: APIClient, make_user):
    """A Microsoft login matching an existing account's email links it instead of duplicating it."""
    existing_user = make_user(username="janedoe", email="jane.doe@contoso.com")
    url = reverse("oauth-microsoft")

    with (
        patch(
            "users.oauth_microsoft._confidential_client",
            return_value=_mock_confidential_client(),
        ),
        patch("users.oauth_microsoft.requests.get", side_effect=_mock_graph_get(has_photo=True)),
    ):
        response = api_client.post(url, {"code": "auth-code"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert User.objects.filter(email="jane.doe@contoso.com").count() == 1
    assert response.data["user"]["id"] == existing_user.pk
    assert OAuthUser.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        user=existing_user, provider="microsoft"
    ).exists()


def test_microsoft_oauth_with_invalid_code_returns_400(api_client: APIClient):
    url = reverse("oauth-microsoft")

    with patch(
        "users.oauth_microsoft._confidential_client",
        return_value=_mock_confidential_client(access_token=None),
    ):
        response = api_client.post(url, {"code": "bad-code"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(email="jane.doe@contoso.com").exists()


def test_microsoft_oauth_requires_code(api_client: APIClient):
    url = reverse("oauth-microsoft")

    response = api_client.post(url, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_microsoft_oauth_rejects_get_requests(api_client: APIClient):
    url = reverse("oauth-microsoft")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
