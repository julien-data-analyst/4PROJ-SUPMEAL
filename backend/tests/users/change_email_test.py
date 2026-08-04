import pytest
from django.urls import reverse
from rest_framework import status

from tests.users.conftest import APIClient
from users.models import OAuthUser, User

pytestmark = pytest.mark.django_db

##########################################-
# Tests for the self-service change-email route
##########################################-


def test_change_email_requires_authentication(api_client: APIClient):
    url = reverse("change-email")

    response = api_client.post(url, {"new_email": "new@example.com"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_email_with_unique_email_succeeds(auth_client: APIClient, regular_user: User):
    url = reverse("change-email")

    response = auth_client.post(url, {"new_email": "alice.new@example.com"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["oauth_unlinked"] is False
    regular_user.refresh_from_db()
    assert regular_user.email == "alice.new@example.com"


def test_change_email_rejects_email_already_used_by_another_user(
    auth_client: APIClient, regular_user: User, other_user: User
):
    url = reverse("change-email")

    response = auth_client.post(url, {"new_email": other_user.email}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    regular_user.refresh_from_db()
    assert regular_user.email != other_user.email


def test_change_email_rejects_get_requests(auth_client: APIClient):
    url = reverse("change-email")

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_oauth_user_can_change_email_with_a_new_password(
    api_client: APIClient, oauth_user: User
):
    """Changing an OAuth-only account's email also requires (and sets) a local password,
    and unlinks every OAuth identity - the account becomes local-only."""
    api_client.force_authenticate(user=oauth_user)
    url = reverse("change-email")

    response = api_client.post(
        url,
        {"new_email": "new@contoso.com", "new_password": "C0mplexPassw0rd!"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["oauth_unlinked"] is True
    oauth_user.refresh_from_db()
    assert oauth_user.email == "new@contoso.com"
    assert oauth_user.check_password("C0mplexPassw0rd!")
    assert not OAuthUser.objects.filter(user=oauth_user).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_oauth_user_changing_email_without_new_password_fails(
    api_client: APIClient, oauth_user: User
):
    api_client.force_authenticate(user=oauth_user)
    url = reverse("change-email")

    response = api_client.post(url, {"new_email": "new@contoso.com"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    oauth_user.refresh_from_db()
    assert oauth_user.email != "new@contoso.com"
    assert OAuthUser.objects.filter(user=oauth_user).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_oauth_user_changing_email_with_a_weak_password_fails(
    api_client: APIClient, oauth_user: User
):
    api_client.force_authenticate(user=oauth_user)
    url = reverse("change-email")

    response = api_client.post(
        url, {"new_email": "new@contoso.com", "new_password": "short"}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    oauth_user.refresh_from_db()
    assert oauth_user.email != "new@contoso.com"
    assert OAuthUser.objects.filter(user=oauth_user).exists()  # pyright: ignore[reportAttributeAccessIssue]
