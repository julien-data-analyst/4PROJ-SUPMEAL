import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from cookbooks.models import Cookbook, SharedUserCookbook
from messaging.models import Message
from planning.models import Planning, RecipePlanning
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    Step,
    Tag,
    UserPreference,
)
from tests.users.conftest import APIClient
from users.models import OAuthUser, User

pytestmark = pytest.mark.django_db

#####################################################-
# Tests for the account-deletion cascade
#
# The schema PROTECTs every FK to User (directly, and via cookbooks a user
# owns), so deleting an account that owns content must be unwound in the
# right order (see users.services.delete_user_account) or it 500s.
#####################################################-


def test_user_can_delete_account_with_owned_content(
    auth_client: APIClient, regular_user: User, other_user: User
):
    ingredient = Ingredient.objects.create(name="Sel")  # pyright: ignore[reportAttributeAccessIssue]
    tag = Tag.objects.create(name="Plat", type="repas")  # pyright: ignore[reportAttributeAccessIssue]

    personal_recipe = Recipe.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        title="Recette perso", creator=regular_user
    )
    RecipeIngredient.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=personal_recipe, ingredient=ingredient, quantity=1, unity="g", person_numbers=1
    )
    RecipeTag.objects.create(recipe=personal_recipe, tag=tag)  # pyright: ignore[reportAttributeAccessIssue]
    Step.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=personal_recipe,
        description="Cuire",
        step_number=1,
        dury=timezone.now(),
        type="cook",
    )

    cookbook = Cookbook.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        name="Mon carnet", creator=regular_user
    )
    cookbook_recipe = Recipe.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        title="Recette du carnet", creator=regular_user, cookbook=cookbook
    )
    planning = Planning.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        name="Semaine", creator=regular_user, cookbook=cookbook
    )
    recipe_planning = RecipePlanning.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        recipe=cookbook_recipe, planning=planning, type="cook", lunch="midi", dayofweek="lundi"
    )
    SharedUserCookbook.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=cookbook, user=other_user, role="editor"
    )
    message = Message.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        author=regular_user, cookbook=cookbook, canal="general", content="Bonjour"
    )

    other_recipe = Recipe.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        title="Recette de Bob", creator=other_user
    )
    fav_by_other = FavoriteRecipe.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        user=other_user, recipe=personal_recipe
    )
    fav_by_self = FavoriteRecipe.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        user=regular_user, recipe=other_recipe
    )
    preference = UserPreference.objects.create(user=regular_user, tag=tag)  # pyright: ignore[reportAttributeAccessIssue]

    url = reverse("user-detail", kwargs={"pk": regular_user.pk})
    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(pk=regular_user.pk).exists()

    assert not Recipe.objects.filter(pk__in=[personal_recipe.pk, cookbook_recipe.pk]).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not Cookbook.objects.filter(pk=cookbook.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not Planning.objects.filter(pk=planning.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not RecipePlanning.objects.filter(pk=recipe_planning.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook_id=cookbook.pk
    ).exists()
    assert not Message.objects.filter(pk=message.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not UserPreference.objects.filter(pk=preference.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert not FavoriteRecipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        pk__in=[fav_by_other.pk, fav_by_self.pk]
    ).exists()

    # Ingredient/Tag are shared master data, never deleted by the cascade.
    assert Ingredient.objects.filter(pk=ingredient.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert Tag.objects.filter(pk=tag.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]

    # other_user and their own untouched content survive.
    assert User.objects.filter(pk=other_user.pk).exists()
    assert Recipe.objects.filter(pk=other_recipe.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]


def test_delete_account_also_removes_other_users_content_inside_owned_cookbook(
    auth_client: APIClient, regular_user: User, other_user: User
):
    """A cookbook-mate's recipe filed inside the deleted user's *owned*
    cookbook is removed too - this is an intentional consequence of the
    all-PROTECT schema (the cookbook can't survive with a dangling recipe,
    and the cookbook can't survive the owner's deletion either), not a bug.
    """
    cookbook = Cookbook.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        name="Carnet partagé", creator=regular_user
    )
    SharedUserCookbook.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        cookbook=cookbook, user=other_user, role="editor"
    )
    contribution = Recipe.objects.create(  # pyright: ignore[reportAttributeAccessIssue]
        title="Contribution de Bob", creator=other_user, cookbook=cookbook
    )

    url = reverse("user-detail", kwargs={"pk": regular_user.pk})
    response = auth_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Recipe.objects.filter(pk=contribution.pk).exists()  # pyright: ignore[reportAttributeAccessIssue]
    assert User.objects.filter(pk=other_user.pk).exists()


def test_user_with_oauth_account_can_delete_account(api_client: APIClient, oauth_user: User):
    api_client.force_authenticate(user=oauth_user)
    url = reverse("user-detail", kwargs={"pk": oauth_user.pk})

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(pk=oauth_user.pk).exists()
    assert not OAuthUser.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
        user_id=oauth_user.pk
    ).exists()
