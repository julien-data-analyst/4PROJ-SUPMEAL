import pytest
from django.urls import reverse
from rest_framework import status

from tests.users.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

#############################################-
# Tests for user registration, login, and profile access
#############################################-


def test_register_creates_user_with_hashed_password(api_client: APIClient):
    """Test that registering a new user creates a user with a hashed password and returns tokens."""
    url = reverse("user-register")
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "C0mplexPassw0rd!",
        "first_name": "New",
        "last_name": "User",
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert "password" not in response.data["user"]
    assert "access" in response.data
    assert "refresh" in response.data

    user = User.objects.get(username="newuser")
    assert user.password != payload["password"]
    assert user.password.startswith("pbkdf2_")
    assert user.check_password(payload["password"])


def test_register_without_profile_icon_defaults_to_empty(api_client: APIClient):
    """Test that registering without a profile icon defaults profile_icon to an empty string."""
    url = reverse("user-register")
    payload = {
        "username": "iconless",
        "email": "iconless@example.com",
        "password": "C0mplexPassw0rd!",
        "first_name": "No",
        "last_name": "Icon",
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["user"]["profile_icon"] == ""


def test_register_rejects_email_already_in_use(api_client: APIClient, regular_user: User):
    url = reverse("user-register")

    response = api_client.post(
        url,
        {"username": "someoneelse", "email": regular_user.email, "password": "C0mplexPassw0rd!"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(username="someoneelse").exists()


def test_register_rejects_email_already_in_use_with_different_case(
    api_client: APIClient, regular_user: User
):
    """Test that registration email uniqueness is case-insensitive, matching
    ChangeEmailSerializer - "Alice@Example.com" can't duplicate "alice@example.com"."""
    url = reverse("user-register")

    response = api_client.post(
        url,
        {
            "username": "someoneelse",
            "email": str(regular_user.email).upper(),
            "password": "C0mplexPassw0rd!",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not User.objects.filter(username="someoneelse").exists()


def test_login_with_correct_credentials_returns_tokens(
    api_client: APIClient, regular_user: User, test_password: str
):
    """Test that logging in with correct credentials returns access and refresh tokens."""
    url = reverse("user-login")

    response = api_client.post(
        url, {"email": regular_user.email, "password": test_password}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["user"]["username"] == regular_user.username
    assert "access" in response.data
    assert "refresh" in response.data


def test_login_with_wrong_password_is_rejected(api_client: APIClient, regular_user: User):
    """Test that logging in with an incorrect password returns a 400 Bad Request."""
    url = reverse("user-login")

    response = api_client.post(
        url, {"email": regular_user.email, "password": "wrong-password"}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_rejects_get_requests(api_client: APIClient):
    """Test that the login endpoint does not accept GET requests."""
    url = reverse("user-login")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_login_is_throttled_after_too_many_attempts(api_client: APIClient):
    """Test that repeated login attempts are rate-limited (brute-force protection)."""
    from config.settings import REST_FRAMEWORK

    rate = REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["auth"]
    limit = int(rate.split("/")[0])
    url = reverse("user-login")

    for _ in range(limit):
        response = api_client.post(
            url, {"email": "nobody@example.com", "password": "wrong"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = api_client.post(
        url, {"email": "nobody@example.com", "password": "wrong"}, format="json"
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_me_requires_authentication(api_client: APIClient):
    """Test that the /me endpoint requires authentication and returns 401 for anonymous users."""
    url = reverse("user-me")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_returns_own_profile(auth_client: APIClient, regular_user: User):
    """Test that the /me endpoint returns the authenticated user's profile."""
    url = reverse("user-me")

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["id"] == regular_user.pk
    assert response.data["email"] == regular_user.email


def test_user_can_update_own_profile(auth_client: APIClient, regular_user: User):
    url = reverse("user-detail", kwargs={"pk": regular_user.pk})

    response = auth_client.patch(url, {"first_name": "Updated"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    regular_user.refresh_from_db()
    assert regular_user.first_name == "Updated"


def test_user_can_delete_own_account(auth_client: APIClient, regular_user: User):
    url = reverse("user-detail", kwargs={"pk": regular_user.pk})

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(pk=regular_user.pk).exists()
