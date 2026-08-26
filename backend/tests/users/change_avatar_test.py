import base64

import pytest
from django.urls import reverse
from rest_framework import status

from tests.users.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

###########################################-
# Tests for the self-service change-avatar route
###########################################-

PNG_DATA_URI = (
    "data:image/png;base64,"
    + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"fake-rest-of-png-data").decode()
)
JPEG_DATA_URI = (
    "data:image/jpeg;base64,"
    + base64.b64encode(b"\xff\xd8\xff" + b"fake-rest-of-jpeg-data").decode()
)
SVG_DATA_URI = (
    "data:image/svg+xml;base64,"
    + base64.b64encode(b"<svg xmlns='http://www.w3.org/2000/svg'></svg>").decode()
)
GIF_DATA_URI = "data:image/gif;base64," + base64.b64encode(b"GIF89a-fake-gif-data").decode()
MISMATCHED_DATA_URI = (
    "data:image/png;base64," + base64.b64encode(b"\xff\xd8\xff" + b"actually-jpeg-bytes").decode()
)


@pytest.mark.parametrize("data_uri", [PNG_DATA_URI, JPEG_DATA_URI, SVG_DATA_URI])
def test_change_avatar_with_allowed_image_type_succeeds(
    auth_client: APIClient, regular_user: User, data_uri: str
):
    url = reverse("change-avatar")

    response = auth_client.post(url, {"avatar": data_uri}, format="json")

    assert response.status_code == status.HTTP_200_OK
    regular_user.refresh_from_db()
    assert regular_user.profile_icon == data_uri


def test_change_avatar_rejects_disallowed_mime_type(auth_client: APIClient, regular_user: User):
    url = reverse("change-avatar")

    response = auth_client.post(url, {"avatar": GIF_DATA_URI}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    regular_user.refresh_from_db()
    assert regular_user.profile_icon != GIF_DATA_URI


def test_change_avatar_rejects_mime_and_content_mismatch(
    auth_client: APIClient, regular_user: User
):
    url = reverse("change-avatar")

    response = auth_client.post(url, {"avatar": MISMATCHED_DATA_URI}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    regular_user.refresh_from_db()
    assert regular_user.profile_icon != MISMATCHED_DATA_URI


def test_change_avatar_requires_authentication(api_client: APIClient):
    url = reverse("change-avatar")

    response = api_client.post(url, {"avatar": PNG_DATA_URI}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_oauth_user_can_change_avatar(api_client: APIClient, oauth_user: User):
    """An OAuth account can override the avatar synced from its provider."""
    api_client.force_authenticate(user=oauth_user)
    url = reverse("change-avatar")

    response = api_client.post(url, {"avatar": PNG_DATA_URI}, format="json")

    assert response.status_code == status.HTTP_200_OK
    oauth_user.refresh_from_db()
    assert oauth_user.profile_icon == PNG_DATA_URI
