import base64
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

# A 1x1 white JPEG - real bytes, since the photo endpoint's response content
# gets base64-encoded into a data URI rather than just having its status
# checked.
FAKE_PHOTO_BYTES = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkI"
    "CQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2wBDAQMDAwQDBAgEBAgQCwkLEBAQEBAQ"
    "EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAABAAEDASIA"
    "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAj/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
    "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX"
    "/9k="
)
FAKE_PHOTO_B64 = base64.b64encode(FAKE_PHOTO_BYTES).decode("ascii")


def _mock_response(
    *,
    ok: bool = True,
    status_code: int = 200,
    json_data=None,
    text: str = "",
    content: bytes = b"",
    headers: dict | None = None,
):
    response = MagicMock()
    response.ok = ok
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = text
    response.content = content
    response.headers = headers or {}
    return response


def _mock_graph_get(*, has_photo: bool):
    def _get(url: str, *args, **kwargs):
        if url == GRAPH_ME_URL:
            return _mock_response(json_data=MICROSOFT_PROFILE)
        if url == GRAPH_PHOTO_URL:
            if has_photo:
                return _mock_response(
                    content=FAKE_PHOTO_BYTES, headers={"Content-Type": "image/jpeg"}
                )
            return _mock_response(ok=False, status_code=404)
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
    assert user.profile_icon == f"data:image/jpeg;base64,{FAKE_PHOTO_B64}"
    assert not user.has_usable_password()

    oauth_account = OAuthUser.objects.get(  # pyright: ignore[reportAttributeAccessIssue]
        user=user, provider="microsoft"
    )
    assert oauth_account.domain == "contoso.com"
    assert oauth_account.profile_icon == f"data:image/jpeg;base64,{FAKE_PHOTO_B64}"


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


def test_microsoft_oauth_refreshes_profile_icon_on_existing_user(
    api_client: APIClient, make_user
):
    """A re-login must refresh an existing account's stale/broken photo, not just
    the linked OAuthUser's - this used to only ever set User.profile_icon at
    account creation, so a value set before photo-fetching worked (or before the
    account had a photo at all) never got corrected on subsequent logins."""
    existing_user = make_user(
        username="janedoe", email="jane.doe@contoso.com", profile_icon="stale-value"
    )
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
    existing_user.refresh_from_db()
    assert existing_user.profile_icon == f"data:image/jpeg;base64,{FAKE_PHOTO_B64}"


def test_microsoft_oauth_links_to_existing_user_by_email_case_insensitively(
    api_client: APIClient, make_user
):
    """Matching by email must be case-insensitive, or a differently-cased Microsoft
    profile email would create a duplicate account instead of linking to the existing
    one - see UserRegisterSerializer.validate_email for the same rule at registration."""
    existing_user = make_user(username="janedoe", email="Jane.Doe@Contoso.com")
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
    assert User.objects.filter(email__iexact="jane.doe@contoso.com").count() == 1
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


##########################################################-
# Tests for linking Microsoft OAuth to an already-authenticated account
##########################################################-


def test_link_microsoft_requires_authentication(api_client: APIClient):
    url = reverse("oauth-microsoft-link")

    response = api_client.post(url, {"code": "auth-code"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_local_user_can_link_microsoft_account(api_client: APIClient, regular_user: User):
    """Linking syncs the account's email to the Microsoft profile's and makes its local
    password unusable - it can only sign in via Microsoft afterwards."""
    api_client.force_authenticate(user=regular_user)
    url = reverse("oauth-microsoft-link")

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
    assert response.data["user"]["id"] == regular_user.pk

    regular_user.refresh_from_db()
    assert regular_user.email == "jane.doe@contoso.com"
    assert not regular_user.has_usable_password()
    oauth_account = OAuthUser.objects.get(  # pyright: ignore[reportAttributeAccessIssue]
        user=regular_user, provider="microsoft"
    )
    assert oauth_account.domain == "contoso.com"


def test_linking_microsoft_account_already_used_by_another_user_fails(
    api_client: APIClient, regular_user: User, make_user
):
    """Linking must not silently steal or merge with another account's email."""
    make_user(username="janedoe", email="jane.doe@contoso.com")
    api_client.force_authenticate(user=regular_user)
    url = reverse("oauth-microsoft-link")

    with (
        patch(
            "users.oauth_microsoft._confidential_client",
            return_value=_mock_confidential_client(),
        ),
        patch("users.oauth_microsoft.requests.get", side_effect=_mock_graph_get(has_photo=True)),
    ):
        response = api_client.post(url, {"code": "auth-code"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    regular_user.refresh_from_db()
    assert regular_user.email != "jane.doe@contoso.com"
    assert regular_user.has_usable_password()
    assert not OAuthUser.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        user=regular_user
    ).exists()


def test_link_microsoft_rejects_get_requests(auth_client: APIClient):
    url = reverse("oauth-microsoft-link")

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
