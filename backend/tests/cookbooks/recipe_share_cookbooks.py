import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from recipes.models import FavoriteRecipe, Recipe
from tests.cookbooks.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

#####################################################################-
# Permission matrix for a Recipe filed in a cookbook, across every role
#####################################################################-

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
def test_create_recipe_in_cookbook_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, role: str
):
    """Test that only the admin/creator roles can file a new recipe into a shared cookbook."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    url = reverse("recipe-list")

    response = auth_client.post(
        url, {"title": "Nouvelle recette", "cookbook": cookbook.pk}, format="json"
    )

    if role in CAN_CREATE:
        assert response.status_code == status.HTTP_201_CREATED
        assert Recipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=cookbook, title="Nouvelle recette"
        ).exists()
    else:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Recipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=cookbook, title="Nouvelle recette"
        ).exists()


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_update_recipe_in_cookbook_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, other_user: User, role: str
):
    """Test that the admin/creator/editor roles can edit an existing recipe in a shared cookbook."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    recipe = Recipe(title="Recette existante", creator=other_user, cookbook=cookbook)
    recipe.save()
    url = reverse("recipe-detail", kwargs={"pk": recipe.pk})

    response = auth_client.patch(url, {"title": "Renommee"}, format="json")

    if role in CAN_EDIT:
        assert response.status_code == status.HTTP_200_OK
        recipe.refresh_from_db()
        assert recipe.title == "Renommee"
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        recipe.refresh_from_db()
        assert recipe.title == "Recette existante"


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_delete_recipe_in_cookbook_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, other_user: User, role: str
):
    """Test that only the admin/creator roles can delete an existing recipe in a shared cookbook."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    recipe = Recipe(title="Recette a supprimer", creator=other_user, cookbook=cookbook)
    recipe.save()
    url = reverse("recipe-detail", kwargs={"pk": recipe.pk})

    response = auth_client.delete(url)

    if role in CAN_DELETE:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Recipe.objects.filter(pk=recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Recipe.objects.filter(pk=recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_read_recipe_in_cookbook_by_role(
    request: pytest.FixtureRequest, auth_client: APIClient, other_user: User, role: str
):
    """Test that every role, including reader/commentator, can read a recipe in the cookbook."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    recipe = Recipe(title="Recette lisible", creator=other_user, cookbook=cookbook)
    recipe.save()
    url = reverse("recipe-detail", kwargs={"pk": recipe.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert response.data["id"] == recipe.pk


###########################################################################-
# Favoriting a recipe filed in a shared cookbook, regardless of the caller's role
###########################################################################-


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_any_role_can_favorite_a_recipe_in_a_shared_cookbook(
    request: pytest.FixtureRequest,
    auth_client: APIClient,
    regular_user: User,
    other_user: User,
    role: str,
):
    """Test that favoriting doesn't require any particular role - even a reader can do it."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    recipe = Recipe(title="Recette a favoriser", creator=other_user, cookbook=cookbook)
    recipe.save()
    url = reverse("recipe-favorite", kwargs={"pk": recipe.pk})

    response = auth_client.post(url)

    assert response.status_code == status.HTTP_201_CREATED
    assert FavoriteRecipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        user=regular_user, recipe=recipe
    ).exists()


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_any_role_can_unfavorite_a_recipe_in_a_shared_cookbook(
    request: pytest.FixtureRequest,
    auth_client: APIClient,
    regular_user: User,
    other_user: User,
    role: str,
):
    """Test that un-favoriting also doesn't require any particular role."""
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    recipe = Recipe(title="Recette a defavoriser", creator=other_user, cookbook=cookbook)
    recipe.save()
    FavoriteRecipe.objects.create(user=regular_user, recipe=recipe)  # pyright: ignore[reportAttributeAccessIssue]
    url = reverse("recipe-favorite", kwargs={"pk": recipe.pk})

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FavoriteRecipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        user=regular_user, recipe=recipe
    ).exists()


@pytest.mark.parametrize("role", ROLE_FIXTURES)
def test_favorited_recipe_in_shared_cookbook_appears_in_recipe_list_regardless_of_role(
    request: pytest.FixtureRequest,
    auth_client: APIClient,
    regular_user: User,
    other_user: User,
    role: str,
):
    """Test that ``?favorite=true`` and ``is_favorite`` surface a favorite from any shared
    cookbook, regardless of the caller's role on it.
    """
    cookbook: Cookbook = request.getfixturevalue(ROLE_FIXTURES[role])
    recipe = Recipe(title="Recette partagee favorite", creator=other_user, cookbook=cookbook)
    recipe.save()
    FavoriteRecipe.objects.create(user=regular_user, recipe=recipe)  # pyright: ignore[reportAttributeAccessIssue]

    detail_response = auth_client.get(reverse("recipe-detail", kwargs={"pk": recipe.pk}))
    list_response = auth_client.get(reverse("recipe-list"), {"favorite": "true"})

    assert detail_response.data is not None
    assert detail_response.data["is_favorite"] is True
    assert list_response.data is not None
    result_ids = [item["id"] for item in list_response.data["results"]]
    assert recipe.pk in result_ids
    matching = next(item for item in list_response.data["results"] if item["id"] == recipe.pk)
    assert matching["is_favorite"] is True


def test_stranger_cannot_read_recipe_in_private_cookbook(
    stranger_client: APIClient, other_users_cookbook: Cookbook, other_user: User
):
    """Test that a user with no share on the cookbook gets a 404 (not visible), not a leaky 403."""
    recipe = Recipe(title="Recette privee", creator=other_user, cookbook=other_users_cookbook)
    recipe.save()
    url = reverse("recipe-detail", kwargs={"pk": recipe.pk})

    response = stranger_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
