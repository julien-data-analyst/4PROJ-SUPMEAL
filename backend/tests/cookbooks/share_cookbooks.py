import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook, SharedUserCookbook
from tests.cookbooks.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

#####################################################-
# Tests for the cookbook "share" action and its roles
#####################################################-


def test_admin_can_share_cookbook_with_multiple_users_and_roles(
    auth_client: APIClient, owned_cookbook: Cookbook, other_user: User, stranger: User
):
    """Test that the admin can share a cookbook with several users at once, each with their role."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(
        url,
        {
            "shares": [
                {"user": other_user.pk, "role": "editor"},
                {"user": stranger.pk, "role": "reader"},
            ]
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    roles = {item["user"]["id"]: item["role"] for item in response.data["shared_with"]}
    assert roles[other_user.pk] == "editor"
    assert roles[stranger.pk] == "reader"
    assert SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=owned_cookbook, user=other_user, role="editor"
    ).exists()
    assert SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=owned_cookbook, user=stranger, role="reader"
    ).exists()


def test_resharing_updates_role_instead_of_duplicating(
    auth_client: APIClient, owned_cookbook: Cookbook, other_user: User
):
    """Test that sharing again with the same user changes their role, not a second row."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})
    auth_client.post(url, {"shares": [{"user": other_user.pk, "role": "reader"}]}, format="json")

    response = auth_client.post(
        url, {"shares": [{"user": other_user.pk, "role": "editor"}]}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    shares = SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=owned_cookbook, user=other_user
    )
    assert shares.count() == 1
    assert shares.get().role == "editor"


def test_admin_can_change_a_users_role_via_patch(
    auth_client: APIClient, owned_cookbook: Cookbook, other_user: User
):
    """Test that PATCH on the share route changes an existing role, same as POST."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})
    auth_client.post(url, {"shares": [{"user": other_user.pk, "role": "reader"}]}, format="json")

    response = auth_client.patch(
        url, {"shares": [{"user": other_user.pk, "role": "editor"}]}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    shares = SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=owned_cookbook, user=other_user
    )
    assert shares.count() == 1
    assert shares.get().role == "editor"


def test_sharing_with_invalid_role_is_rejected(
    auth_client: APIClient, owned_cookbook: Cookbook, other_user: User
):
    """Test that an unknown role value is rejected with a 400 response."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(
        url, {"shares": [{"user": other_user.pk, "role": "superadmin"}]}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=owned_cookbook, user=other_user
    ).exists()


def test_sharing_with_the_cookbook_creator_is_rejected(
    auth_client: APIClient, owned_cookbook: Cookbook, regular_user: User
):
    """Test that the admin can't grant themselves a shared role - they already have full rights."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(
        url, {"shares": [{"user": regular_user.pk, "role": "reader"}]}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_admin_can_share_cookbook_with_a_user_by_email(
    auth_client: APIClient, owned_cookbook: Cookbook, other_user: User
):
    """Test that ``shares[].email`` grants access to the matching user, just like ``user``."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(
        url, {"shares": [{"email": other_user.email, "role": "editor"}]}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["shared_with"][0]["user"]["id"] == other_user.pk
    assert SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=owned_cookbook, user=other_user, role="editor"
    ).exists()


def test_share_by_email_is_case_insensitive(
    auth_client: APIClient, owned_cookbook: Cookbook, other_user: User
):
    """Test that the email lookup ignores case, e.g. an uppercased domain still matches."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(
        url, {"shares": [{"email": other_user.email.upper(), "role": "reader"}]}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=owned_cookbook, user=other_user, role="reader"
    ).exists()


def test_share_by_unknown_email_is_rejected(auth_client: APIClient, owned_cookbook: Cookbook):
    """Test that sharing with an email matching no user is a 400, not a silent no-op."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(
        url,
        {"shares": [{"email": "unknown@example.com", "role": "reader"}]},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not SharedUserCookbook.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_share_with_both_user_and_email_is_rejected(
    auth_client: APIClient, owned_cookbook: Cookbook, other_user: User
):
    """Test that providing both ``user`` and ``email`` in the same entry is rejected."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(
        url,
        {"shares": [{"user": other_user.pk, "email": other_user.email, "role": "reader"}]},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not SharedUserCookbook.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_share_with_neither_user_nor_email_is_rejected(
    auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test that an entry missing both ``user`` and ``email`` is rejected."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(url, {"shares": [{"role": "reader"}]}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_non_admin_cannot_share_cookbook(
    auth_client: APIClient, cookbook_shared_as_editor: Cookbook, stranger: User
):
    """Test that a shared member (e.g. editor) cannot grant access to others - only admin can."""
    url = reverse("cookbook-share", kwargs={"pk": cookbook_shared_as_editor.pk})

    response = auth_client.post(
        url, {"shares": [{"user": stranger.pk, "role": "reader"}]}, format="json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=cookbook_shared_as_editor, user=stranger
    ).exists()


def test_anonymous_user_cannot_share_cookbook(
    api_client: APIClient, owned_cookbook: Cookbook, other_user: User
):
    """Test that an anonymous user cannot share a cookbook and receives a 401 response."""
    url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})

    response = api_client.post(
        url, {"shares": [{"user": other_user.pk, "role": "reader"}]}, format="json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


####################################################-
# Tests for revoking access via the "unshare" action
####################################################-


def test_admin_can_unshare_one_or_more_users(
    auth_client: APIClient, owned_cookbook: Cookbook, other_user: User, stranger: User
):
    """Test that the admin can revoke several users' access to a cookbook in one call."""
    share_url = reverse("cookbook-share", kwargs={"pk": owned_cookbook.pk})
    auth_client.post(
        share_url,
        {
            "shares": [
                {"user": other_user.pk, "role": "editor"},
                {"user": stranger.pk, "role": "reader"},
            ]
        },
        format="json",
    )
    unshare_url = reverse("cookbook-unshare", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(unshare_url, {"users": [other_user.pk, stranger.pk]}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["shared_with"] == []
    assert not SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=owned_cookbook, user__in=[other_user, stranger]
    ).exists()


def test_unsharing_a_user_with_no_access_is_a_noop(
    auth_client: APIClient, owned_cookbook: Cookbook, other_user: User
):
    """Test that revoking a user who was never shared the cookbook doesn't error."""
    url = reverse("cookbook-unshare", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.post(url, {"users": [other_user.pk]}, format="json")

    assert response.status_code == status.HTTP_200_OK


def test_non_admin_cannot_unshare_cookbook(
    auth_client: APIClient, cookbook_shared_as_editor: Cookbook, regular_user: User
):
    """Test that a shared member (e.g. editor) cannot revoke access - only admin can."""
    url = reverse("cookbook-unshare", kwargs={"pk": cookbook_shared_as_editor.pk})

    response = auth_client.post(url, {"users": [regular_user.pk]}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=cookbook_shared_as_editor, user=regular_user
    ).exists()


def test_anonymous_user_cannot_unshare_cookbook(
    api_client: APIClient, owned_cookbook: Cookbook, other_user: User
):
    """Test that an anonymous user cannot revoke a cookbook's shares and receives a 401."""
    url = reverse("cookbook-unshare", kwargs={"pk": owned_cookbook.pk})

    response = api_client.post(url, {"users": [other_user.pk]}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
