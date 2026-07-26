import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from messaging.models import Message
from recipes.models import Recipe
from tests.messaging.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

##########################################################################-
# Permission matrix for cookbook/recipe message channels, across every role
##########################################################################-

ROLE_FIXTURES = {
    "admin": "owned_cookbook",
    "creator": "cookbook_shared_as_creator",
    "editor": "cookbook_shared_as_editor",
    "commentator": "cookbook_shared_as_commentator",
    "reader": "cookbook_shared_as_reader",
}
CAN_COMMENT = {"admin", "creator", "editor", "commentator"}


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_post_cookbook_global_message_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, message_payload: dict, role: str
):
    """Test that every role except reader can post in a cookbook's global channel."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    url = reverse("cookbook-message-list", kwargs={"cookbook_pk": cookbook.pk})

    response = auth_client.post(url, message_payload, format="json")

    if role in CAN_COMMENT:
        assert response.status_code == status.HTTP_201_CREATED
        assert Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=cookbook, recipe__isnull=True
        ).exists()
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=cookbook, recipe__isnull=True
        ).exists()


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_post_recipe_message_by_role(
    request: pytest.FixtureRequest,
    auth_client: APIClient,
    other_user: User,
    message_payload: dict,
    role: str,
):
    """Test that every role except reader can post in a specific recipe's channel."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    recipe = Recipe(title="Recette a commenter", creator=other_user, cookbook=cookbook)
    recipe.save()
    url = reverse(
        "recipe-message-list", kwargs={"cookbook_pk": cookbook.pk, "recipe_pk": recipe.pk}
    )

    response = auth_client.post(url, message_payload, format="json")

    if role in CAN_COMMENT:
        assert response.status_code == status.HTTP_201_CREATED
        assert Message.objects.filter(recipe=recipe).exists()  # pyright: ignore[reportAttributeAccessIssue]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            recipe=recipe
        ).exists()


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_read_cookbook_global_messages_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, other_user: User, role: str
):
    """Test that every role, including reader, can read the cookbook's global channel."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    Message(
        content="Message existant", canal="general", author=other_user, cookbook=cookbook
    ).save()
    url = reverse("cookbook-message-list", kwargs={"cookbook_pk": cookbook.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["count"] == 1


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_read_recipe_messages_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, other_user: User, role: str
):
    """Test that every role, including reader, can read a specific recipe's channel."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    recipe = Recipe(title="Recette lisible", creator=other_user, cookbook=cookbook)
    recipe.save()
    Message(
        content="Message existant",
        canal="general",
        author=other_user,
        cookbook=cookbook,
        recipe=recipe,
    ).save()
    url = reverse(
        "recipe-message-list", kwargs={"cookbook_pk": cookbook.pk, "recipe_pk": recipe.pk}
    )

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["count"] == 1


#####################################################-
# Who is allowed to delete a message once it's posted
#####################################################-


def test_reader_cannot_delete_someone_elses_message(
    auth_client: APIClient, other_user: User, cookbook_shared_as_reader: Cookbook
):
    """Test that a reader can't delete a message they didn't write."""
    message = Message(
        content="Message de Bob",
        canal="general",
        author=other_user,
        cookbook=cookbook_shared_as_reader,
    )
    message.save()
    url = reverse(
        "cookbook-message-detail",
        kwargs={"cookbook_pk": cookbook_shared_as_reader.pk, "pk": message.pk},
    )

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Message.objects.filter(pk=message.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_commentator_cannot_delete_someone_elses_message(
    auth_client: APIClient, other_user: User, cookbook_shared_as_commentator: Cookbook
):
    """Test that a commentator can post messages but can't delete another member's message."""
    message = Message(
        content="Message de Bob",
        canal="general",
        author=other_user,
        cookbook=cookbook_shared_as_commentator,
    )
    message.save()
    url = reverse(
        "cookbook-message-detail",
        kwargs={"cookbook_pk": cookbook_shared_as_commentator.pk, "pk": message.pk},
    )

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Message.objects.filter(pk=message.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_commentator_can_delete_their_own_message(
    auth_client: APIClient, regular_user: User, cookbook_shared_as_commentator: Cookbook
):
    """Test that a commentator, while unable to moderate others, can delete their own message."""
    message = Message(
        content="Mon message",
        canal="general",
        author=regular_user,
        cookbook=cookbook_shared_as_commentator,
    )
    message.save()
    url = reverse(
        "cookbook-message-detail",
        kwargs={"cookbook_pk": cookbook_shared_as_commentator.pk, "pk": message.pk},
    )

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Message.objects.filter(pk=message.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_cookbook_admin_can_delete_a_members_message(
    other_auth_client: APIClient, regular_user: User, cookbook_shared_as_commentator: Cookbook
):
    """Test that the cookbook's admin (its creator) can moderate: delete any member's message."""
    message = Message(
        content="Message a moderer",
        canal="general",
        author=regular_user,
        cookbook=cookbook_shared_as_commentator,
    )
    message.save()
    url = reverse(
        "cookbook-message-detail",
        kwargs={"cookbook_pk": cookbook_shared_as_commentator.pk, "pk": message.pk},
    )

    response = other_auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Message.objects.filter(pk=message.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


######################################################################-
# Anonymous users and strangers (no share at all on the cookbook/recipe)
######################################################################-


def test_anonymous_user_cannot_list_cookbook_messages(
    api_client: APIClient, owned_cookbook: Cookbook
):
    url = reverse("cookbook-message-list", kwargs={"cookbook_pk": owned_cookbook.pk})

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_anonymous_user_cannot_post_cookbook_message(
    api_client: APIClient, owned_cookbook: Cookbook, message_payload: dict
):
    url = reverse("cookbook-message-list", kwargs={"cookbook_pk": owned_cookbook.pk})

    response = api_client.post(url, message_payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not Message.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_stranger_cannot_list_messages_in_private_cookbook(
    stranger_client: APIClient, other_users_cookbook: Cookbook
):
    """Test that a user with no share on the cookbook gets a 404 (not visible), not a leaky 403."""
    url = reverse("cookbook-message-list", kwargs={"cookbook_pk": other_users_cookbook.pk})

    response = stranger_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_stranger_cannot_post_message_in_private_cookbook(
    stranger_client: APIClient, other_users_cookbook: Cookbook, message_payload: dict
):
    url = reverse("cookbook-message-list", kwargs={"cookbook_pk": other_users_cookbook.pk})

    response = stranger_client.post(url, message_payload, format="json")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert not Message.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_stranger_cannot_access_messages_of_a_recipe_in_a_private_cookbook(
    stranger_client: APIClient, other_user: User, other_users_cookbook: Cookbook
):
    recipe = Recipe(title="Recette privee", creator=other_user, cookbook=other_users_cookbook)
    recipe.save()
    url = reverse(
        "recipe-message-list",
        kwargs={"cookbook_pk": other_users_cookbook.pk, "recipe_pk": recipe.pk},
    )

    response = stranger_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_recipe_message_route_404s_when_recipe_not_in_that_cookbook(
    auth_client: APIClient,
    owned_cookbook: Cookbook,
    other_users_cookbook: Cookbook,
    other_user: User,
):
    """Test that mismatching cookbook_pk/recipe_pk 404s instead of leaking a foreign recipe."""
    foreign_recipe = Recipe(
        title="Recette d'un autre carnet", creator=other_user, cookbook=other_users_cookbook
    )
    foreign_recipe.save()
    url = reverse(
        "recipe-message-list",
        kwargs={"cookbook_pk": owned_cookbook.pk, "recipe_pk": foreign_recipe.pk},
    )

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
