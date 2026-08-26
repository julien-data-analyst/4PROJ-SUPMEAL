import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import DEFAULT_COOKBOOK_ICON, Cookbook, SharedUserCookbook
from messaging.models import Message
from planning.models import Planning
from recipes.models import Recipe
from tests.cookbooks.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db

#################################################################-
# Tests for creating/renaming/deleting a cookbook and its contents
#################################################################-


def test_owner_can_create_cookbook(auth_client: APIClient, regular_user):
    """Test that creating a cookbook sets the caller as its creator/admin."""
    url = reverse("cookbook-list")

    response = auth_client.post(url, {"name": "Mon carnet"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["name"] == "Mon carnet"
    assert response.data["creator"]["id"] == regular_user.pk
    assert response.data["shared_with"] == []


def test_creating_a_cookbook_without_icon_gets_the_hardcoded_default(auth_client: APIClient):
    """Test that a cookbook created without an ``icon`` gets the hard-coded default one."""
    url = reverse("cookbook-list")

    response = auth_client.post(url, {"name": "Mon carnet"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["icon"] == DEFAULT_COOKBOOK_ICON


def test_creating_a_cookbook_with_a_custom_icon_uses_it(auth_client: APIClient):
    """Test that an explicit ``icon`` overrides the hard-coded default."""
    url = reverse("cookbook-list")
    custom_icon = "data:image/png;base64,AAAA"

    response = auth_client.post(url, {"name": "Mon carnet", "icon": custom_icon}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data is not None
    assert response.data["icon"] == custom_icon


def test_owner_can_rename_own_cookbook(auth_client: APIClient, owned_cookbook: Cookbook):
    """Test that the cookbook's admin (its creator) can rename it."""
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.patch(url, {"name": "Nouveau nom"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    owned_cookbook.refresh_from_db()
    assert owned_cookbook.name == "Nouveau nom"


def test_owner_can_delete_own_cookbook(auth_client: APIClient, owned_cookbook: Cookbook):
    """Test that the cookbook's admin can delete it."""
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Cookbook.objects.filter(pk=owned_cookbook.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_deleting_cookbook_with_content_detaches_recipes_and_plannings(
    auth_client: APIClient,
    owned_cookbook: Cookbook,
    regular_user: User,
    other_user: User,
):
    """Test that deleting a cookbook detaches (not deletes) the recipes/plannings filed
    in it, and drops the cookbook-scoped rows (shares, messages) that only made sense in
    it - instead of failing on their PROTECTed `cookbook` FK."""
    recipe = Recipe(title="Recette du carnet", creator=regular_user, cookbook=owned_cookbook)
    recipe.save()
    planning = Planning(name="Planning du carnet", creator=regular_user, cookbook=owned_cookbook)
    planning.save()
    SharedUserCookbook(cookbook=owned_cookbook, user=other_user, role="reader").save()  # pyright: ignore[reportAttributeAccessIssue]
    Message(
        content="Bienvenue", canal="general", author=regular_user, cookbook=owned_cookbook
    ).save()
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Cookbook.objects.filter(pk=owned_cookbook.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    recipe.refresh_from_db()
    planning.refresh_from_db()
    assert recipe.cookbook_id is None  # pyright: ignore[reportAttributeAccessIssue]
    assert Recipe.objects.filter(pk=recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert planning.cookbook_id is None  # pyright: ignore[reportAttributeAccessIssue]
    assert Planning.objects.filter(pk=planning.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook_id=owned_cookbook.pk
    ).exists()
    assert not Message.objects.filter(cookbook_id=owned_cookbook.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_anonymous_user_cannot_create_cookbook(api_client: APIClient):
    """Test that an anonymous user cannot create a cookbook and receives a 401 response."""
    url = reverse("cookbook-list")

    response = api_client.post(url, {"name": "Intrus"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not Cookbook.objects.exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_stranger_cannot_see_or_rename_someone_elses_cookbook(
    other_auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test that a user with no relation to the cookbook can't rename it (404 - not visible)."""
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = other_auth_client.patch(url, {"name": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    owned_cookbook.refresh_from_db()
    assert owned_cookbook.name != "Hacked"


def test_stranger_cannot_delete_someone_elses_cookbook(
    other_auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test that a user with no relation to the cookbook can't delete it (404)."""
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = other_auth_client.delete(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Cookbook.objects.filter(pk=owned_cookbook.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_shared_editor_cannot_rename_cookbook(
    auth_client: APIClient, cookbook_shared_as_editor: Cookbook
):
    """Test that a non-admin member (e.g. editor) can see the cookbook but not rename it (403)."""
    url = reverse("cookbook-detail", kwargs={"pk": cookbook_shared_as_editor.pk})

    response = auth_client.patch(url, {"name": "Hacked"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_owner_can_create_and_delete_recipe_in_own_cookbook(
    auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test the owner's happy path: filing a recipe into their own cookbook, then deleting it."""
    create_url = reverse("recipe-list")

    create_response = auth_client.post(
        create_url, {"title": "Recette du carnet", "cookbook": owned_cookbook.pk}, format="json"
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.data is not None
    recipe_id = create_response.data["id"]
    delete_response = auth_client.delete(reverse("recipe-detail", kwargs={"pk": recipe_id}))

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Recipe.objects.filter(pk=recipe_id).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_owner_can_create_and_delete_planning_in_own_cookbook(
    auth_client: APIClient, owned_cookbook: Cookbook
):
    """Test the owner's happy path: filing a planning into their own cookbook, then deleting it."""
    create_url = reverse("planning-list")

    create_response = auth_client.post(
        create_url, {"name": "Semaine 1", "cookbook": owned_cookbook.pk}, format="json"
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.data is not None
    planning_id = create_response.data["id"]
    delete_response = auth_client.delete(reverse("planning-detail", kwargs={"pk": planning_id}))

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Planning.objects.filter(pk=planning_id).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_cookbook_detail_lists_its_recipes_and_plannings(
    auth_client: APIClient, owned_cookbook: Cookbook, regular_user
):
    """Test that a cookbook's detail response includes the recipes/plannings filed into it."""
    recipe = Recipe(title="Recette du carnet", creator=regular_user, cookbook=owned_cookbook)
    recipe.save()
    planning = Planning(name="Semaine 1", creator=regular_user, cookbook=owned_cookbook)
    planning.save()
    url = reverse("cookbook-detail", kwargs={"pk": owned_cookbook.pk})

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data is not None
    assert [r["id"] for r in response.data["recipes"]] == [recipe.pk]
    assert response.data["recipes"][0]["title"] == "Recette du carnet"
    assert [p["id"] for p in response.data["plannings"]] == [planning.pk]
    assert response.data["plannings"][0]["name"] == "Semaine 1"


##########################################-
# shared_with_me: cookbooks shared with the caller vs. their own
##########################################-


def test_shared_with_me_filter_true_returns_only_cookbooks_shared_with_caller(
    auth_client: APIClient, owned_cookbook: Cookbook, cookbook_shared_as_reader: Cookbook
):
    """Test that ``?shared_with_me=true`` only returns cookbooks shared with the caller,
    not the ones they created themselves.
    """
    url = reverse("cookbook-list")

    response = auth_client.get(url, {"shared_with_me": "true"})

    assert response.data is not None
    names = [item["name"] for item in response.data["results"]]
    assert names == [cookbook_shared_as_reader.name]


def test_shared_with_me_filter_false_returns_only_the_callers_own_cookbooks(
    auth_client: APIClient, owned_cookbook: Cookbook, cookbook_shared_as_reader: Cookbook
):
    """Test that ``?shared_with_me=false`` excludes cookbooks shared with the caller,
    keeping only the ones they created themselves.
    """
    url = reverse("cookbook-list")

    response = auth_client.get(url, {"shared_with_me": "false"})

    assert response.data is not None
    names = [item["name"] for item in response.data["results"]]
    assert names == [owned_cookbook.name]


##########################################-
# role: cookbooks shared with the caller at a specific role
##########################################-


def test_role_filter_returns_only_cookbooks_shared_at_that_role(
    auth_client: APIClient, other_user: User, regular_user: User
):
    """Test that ``?role=editor`` only returns cookbooks shared at exactly that role."""
    editor_cookbook = Cookbook(name="Carnet edite", creator=other_user)
    editor_cookbook.save()
    SharedUserCookbook(
        cookbook=editor_cookbook, user=regular_user, role=SharedUserCookbook.Role.EDITOR
    ).save()

    reader_cookbook = Cookbook(name="Carnet lu", creator=other_user)
    reader_cookbook.save()
    SharedUserCookbook(
        cookbook=reader_cookbook, user=regular_user, role=SharedUserCookbook.Role.READER
    ).save()

    url = reverse("cookbook-list")

    response = auth_client.get(url, {"role": "editor"})

    assert response.data is not None
    names = [item["name"] for item in response.data["results"]]
    assert names == [editor_cookbook.name]


def test_role_filter_creator_does_not_include_the_callers_own_cookbooks(
    auth_client: APIClient, owned_cookbook: Cookbook, cookbook_shared_as_creator: Cookbook
):
    """The caller's own cookbooks (implicit "admin") must not match ``role=creator``,
    the *shared* "creator" role string - see SharedUserCookbook.Role docstring."""
    url = reverse("cookbook-list")

    response = auth_client.get(url, {"role": "creator"})

    assert response.data is not None
    names = [item["name"] for item in response.data["results"]]
    assert names == [cookbook_shared_as_creator.name]
