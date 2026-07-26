import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from messaging.models import Message
from recipes.models import Recipe
from tests.messaging.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

################################################################-
# Tests for a user posting/reading/deleting their own comments,
# both in a cookbook's global channel and in one of its recipes
################################################################-


def test_owner_can_post_message_in_cookbook_global_channel(
    auth_client: APIClient, regular_user: User, owned_cookbook: Cookbook, message_payload: dict
):
    """Test that posting to a cookbook's message list creates a global-channel message."""
    url = reverse("cookbook-message-list", kwargs={"cookbook_pk": owned_cookbook.pk})

    response = auth_client.post(url, message_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["content"] == message_payload["content"]
    assert response.data["author"]["id"] == regular_user.pk
    assert response.data["cookbook"] == owned_cookbook.pk
    assert response.data["recipe"] is None
    assert Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=owned_cookbook, recipe__isnull=True, author=regular_user
    ).exists()


def test_owner_can_list_messages_in_cookbook_global_channel(
    auth_client: APIClient, owned_cookbook: Cookbook, owned_cookbook_message: Message
):
    url = reverse("cookbook-message-list", kwargs={"cookbook_pk": owned_cookbook.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == owned_cookbook_message.pk


def test_owner_can_retrieve_a_message_in_cookbook_global_channel(
    auth_client: APIClient, owned_cookbook: Cookbook, owned_cookbook_message: Message
):
    url = reverse(
        "cookbook-message-detail",
        kwargs={"cookbook_pk": owned_cookbook.pk, "pk": owned_cookbook_message.pk},
    )

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["content"] == owned_cookbook_message.content


def test_owner_can_delete_own_message_in_cookbook_global_channel(
    auth_client: APIClient, owned_cookbook: Cookbook, owned_cookbook_message: Message
):
    url = reverse(
        "cookbook-message-detail",
        kwargs={"cookbook_pk": owned_cookbook.pk, "pk": owned_cookbook_message.pk},
    )

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        pk=owned_cookbook_message.pk
    ).exists()


def test_owner_can_post_message_in_recipe_channel(
    auth_client: APIClient,
    regular_user: User,
    owned_cookbook: Cookbook,
    owned_recipe: Recipe,
    message_payload: dict,
):
    """Test that posting under a recipe's message list ties the message to that recipe."""
    url = reverse(
        "recipe-message-list",
        kwargs={"cookbook_pk": owned_cookbook.pk, "recipe_pk": owned_recipe.pk},
    )

    response = auth_client.post(url, message_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["recipe"] == owned_recipe.pk
    assert response.data["cookbook"] == owned_cookbook.pk
    assert Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=owned_recipe, author=regular_user
    ).exists()


def test_owner_can_list_messages_in_recipe_channel(
    auth_client: APIClient,
    owned_cookbook: Cookbook,
    owned_recipe: Recipe,
    owned_recipe_message: Message,
):
    url = reverse(
        "recipe-message-list",
        kwargs={"cookbook_pk": owned_cookbook.pk, "recipe_pk": owned_recipe.pk},
    )

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == owned_recipe_message.pk


def test_recipe_channel_messages_do_not_leak_into_global_channel(
    auth_client: APIClient, owned_cookbook: Cookbook, owned_recipe_message: Message
):
    """Test that a message posted in a recipe's channel doesn't show up in the
    cookbook's global channel listing (and vice versa - they're separate channels)."""
    url = reverse("cookbook-message-list", kwargs={"cookbook_pk": owned_cookbook.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["count"] == 0


def test_owner_can_retrieve_a_message_in_recipe_channel(
    auth_client: APIClient,
    owned_cookbook: Cookbook,
    owned_recipe: Recipe,
    owned_recipe_message: Message,
):
    url = reverse(
        "recipe-message-detail",
        kwargs={
            "cookbook_pk": owned_cookbook.pk,
            "recipe_pk": owned_recipe.pk,
            "pk": owned_recipe_message.pk,
        },
    )

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["content"] == owned_recipe_message.content


def test_owner_can_delete_own_message_in_recipe_channel(
    auth_client: APIClient,
    owned_cookbook: Cookbook,
    owned_recipe: Recipe,
    owned_recipe_message: Message,
):
    url = reverse(
        "recipe-message-detail",
        kwargs={
            "cookbook_pk": owned_cookbook.pk,
            "recipe_pk": owned_recipe.pk,
            "pk": owned_recipe_message.pk,
        },
    )

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        pk=owned_recipe_message.pk
    ).exists()


def test_message_cannot_be_updated_via_patch(
    auth_client: APIClient, owned_cookbook: Cookbook, owned_cookbook_message: Message
):
    """Test that there is no route to edit a message - even its own author gets a 405."""
    url = reverse(
        "cookbook-message-detail",
        kwargs={"cookbook_pk": owned_cookbook.pk, "pk": owned_cookbook_message.pk},
    )

    response = auth_client.patch(url, {"content": "Modifie"}, format="json")

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    owned_cookbook_message.refresh_from_db()
    assert owned_cookbook_message.content != "Modifie"


def test_message_cannot_be_updated_via_put(
    auth_client: APIClient, owned_cookbook: Cookbook, owned_cookbook_message: Message
):
    """Test that there is no route to fully replace a message either - PUT also 405s."""
    url = reverse(
        "cookbook-message-detail",
        kwargs={"cookbook_pk": owned_cookbook.pk, "pk": owned_cookbook_message.pk},
    )

    response = auth_client.put(url, {"content": "Modifie"}, format="json")

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
