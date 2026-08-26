import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from planning.models import Planning
from tests.cookbooks.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

######################################################################-
# Permission matrix for a Planning filed in a cookbook, across every role
######################################################################-

ROLE_FIXTURES = {
    "admin": "owned_cookbook",
    "creator": "cookbook_shared_as_creator",
    "editor": "cookbook_shared_as_editor",
    "commentator": "cookbook_shared_as_commentator",
    "reader": "cookbook_shared_as_reader",
}
CAN_CREATE = {"admin", "creator"}
CAN_EDIT = {"admin", "creator", "editor"}
CAN_DELETE = {"admin", "creator"}


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_create_planning_in_cookbook_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, role: str
):
    """Test that only the admin/creator roles can file a new planning into a shared cookbook."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    url = reverse("planning-list")

    response = auth_client.post(
        url, {"name": "Nouveau planning", "cookbook": cookbook.pk}, format="json"
    )

    if role in CAN_CREATE:
        assert response.status_code == status.HTTP_201_CREATED
        assert Planning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=cookbook, name="Nouveau planning"
        ).exists()
    else:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Planning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=cookbook, name="Nouveau planning"
        ).exists()


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_update_planning_in_cookbook_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, other_user: User, role: str
):
    """Test that the admin/creator/editor roles can edit an existing planning in the cookbook."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    planning = Planning(name="Planning existant", creator=other_user, cookbook=cookbook)
    planning.save()
    url = reverse("planning-detail", kwargs={"pk": planning.pk})

    response = auth_client.patch(url, {"name": "Renomme"}, format="json")

    if role in CAN_EDIT:
        assert response.status_code == status.HTTP_200_OK
        planning.refresh_from_db()
        assert planning.name == "Renomme"
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        planning.refresh_from_db()
        assert planning.name == "Planning existant"


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_delete_planning_in_cookbook_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, other_user: User, role: str
):
    """Test that only the admin/creator roles can delete an existing planning in the cookbook."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    planning = Planning(name="Planning a supprimer", creator=other_user, cookbook=cookbook)
    planning.save()
    url = reverse("planning-detail", kwargs={"pk": planning.pk})

    response = auth_client.delete(url)

    if role in CAN_DELETE:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Planning.objects.filter(pk=planning.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Planning.objects.filter(pk=planning.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_read_planning_in_cookbook_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, other_user: User, role: str
):
    """Test that every role, including reader/commentator, can read a planning in the cookbook."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    planning = Planning(name="Planning lisible", creator=other_user, cookbook=cookbook)
    planning.save()
    url = reverse("planning-detail", kwargs={"pk": planning.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["id"] == planning.pk


def test_stranger_cannot_read_planning_in_private_cookbook(
    stranger_client: APIClient, other_users_cookbook: Cookbook, other_user: User
):
    """Test that a user with no share on the cookbook gets a 404 (not visible), not a leaky 403."""
    planning = Planning(name="Planning prive", creator=other_user, cookbook=other_users_cookbook)
    planning.save()
    url = reverse("planning-detail", kwargs={"pk": planning.pk})

    response = stranger_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
