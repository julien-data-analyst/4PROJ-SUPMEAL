import pytest
from django.utils import timezone

from cookbooks.models import Cookbook, SharedUserCookbook
from planning.models import Planning, RecipePlanning
from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Step, Tag
from tests.recipes.conftest import (  # noqa: F401
    APIClient,
    api_client,
    auth_client,
    cookbook_shared_with_regular_user,
    make_user,
    other_auth_client,
    other_user,
    owned_recipe,
    recipe_payload,
    regular_user,
    test_password,
)
from users.models import User

#########################################-
# Fixtures for import/export tests
#########################################-


@pytest.fixture
def stranger(make_user) -> User:  # noqa: F811
    """A third user, unrelated to any cookbook/recipe used in a given test."""
    return make_user(username="carol", email="carol@example.com", first_name="Carol", last_name="C")


@pytest.fixture
def stranger_client(api_client: APIClient, stranger: User) -> APIClient:  # noqa: F811
    api_client.force_authenticate(user=stranger)
    return api_client


@pytest.fixture
def other_user_client(other_user: User) -> APIClient:  # noqa: F811
    """An authenticated client for ``other_user``, independent from ``auth_client``.

    Unlike ``other_auth_client`` (which reuses/mutates the same underlying
    ``api_client`` as ``auth_client``, so only the *last*-resolved fixture's
    identity actually applies), this one wraps its own ``APIClient`` - needed
    whenever a test genuinely acts as two different users at once, e.g. an
    export-then-reimport round trip.
    """
    client = APIClient()
    client.force_authenticate(user=other_user)
    return client


@pytest.fixture
def recipe_export_payload() -> dict:
    """A single recipe object in the exact shape produced by the export endpoints."""
    return {
        "title": "Crepes",
        "image": None,
        "source": "https://example.com/crepes",
        "cooking_duration": "15.50",
        "created_at": "2026-07-20T09:00:00Z",
        "updated_at": "2026-07-20T09:00:00Z",
        "tags": [{"name": "Dessert", "type": "repas", "description": None}],
        "ingredients": [
            {
                "name": "Farine",
                "image": None,
                "quantity": "250.00",
                "unity": "g",
                "person_numbers": 4,
            },
        ],
        "steps": [
            {
                "description": "Melanger",
                "step_number": 1,
                "dury": "2026-07-25T00:05:00Z",
                "type": "prep",
            },
        ],
    }


@pytest.fixture
def other_users_private_recipe(other_user: User) -> Recipe:  # noqa: F811
    """A recipe filed into a cookbook created by ``other_user``, not shared with anyone."""
    cookbook = Cookbook(name="Carnet prive de Bob", creator=other_user)
    cookbook.save()
    recipe = Recipe(title="Recette privee", creator=other_user, cookbook=cookbook)
    recipe.save()
    return recipe


@pytest.fixture
def owned_cookbook_with_recipe_and_planning(regular_user: User) -> Cookbook:  # noqa: F811
    """A cookbook owned by ``regular_user`` with one recipe (full ingredients/
    tags/steps) and one planning that schedules that recipe - the shape the
    cookbook export walks.
    """
    cookbook = Cookbook(name="Mon carnet", creator=regular_user)
    cookbook.save()

    recipe = Recipe(title="Crepes", creator=regular_user, cookbook=cookbook)
    recipe.save()
    ingredient = Ingredient(name="Farine")
    ingredient.save()
    RecipeIngredient(
        recipe=recipe, ingredient=ingredient, quantity=250, unity="g", person_numbers=4
    ).save()
    tag = Tag(name="Dessert", type="repas")
    tag.save()
    RecipeTag(recipe=recipe, tag=tag).save()
    Step(
        recipe=recipe,
        description="Melanger",
        step_number=1,
        dury=timezone.now(),
        type="prep",
    ).save()

    planning = Planning(name="Semaine 1", creator=regular_user, cookbook=cookbook)
    planning.save()
    RecipePlanning(
        planning=planning, recipe=recipe, type="plat", lunch="midi", dayofweek="lundi"
    ).save()

    return cookbook


@pytest.fixture
def cookbook_shared_as_reader_with_regular_user(
    other_user: User,  # noqa: F811
    regular_user: User,  # noqa: F811
) -> Cookbook:
    """A cookbook created by ``other_user`` and shared with ``regular_user``
    at the lowest ("reader") role - just enough to read/export it.
    """
    cookbook = Cookbook(name="Carnet de Bob", creator=other_user)
    cookbook.save()
    SharedUserCookbook(
        cookbook=cookbook, user=regular_user, role=SharedUserCookbook.Role.READER
    ).save()
    return cookbook


@pytest.fixture
def cookbook_export_payload() -> dict:
    """A single cookbook object in the exact shape produced by the export endpoints."""
    return {
        "name": "Recettes de famille",
        "recipes": [
            {
                "id": 1,
                "title": "Crepes",
                "image": None,
                "source": "https://example.com/crepes",
                "cooking_duration": "15.50",
                "tags": [{"name": "Dessert", "type": "repas", "description": None}],
                "ingredients": [
                    {
                        "name": "Farine",
                        "image": None,
                        "quantity": "250.00",
                        "unity": "g",
                        "person_numbers": 4,
                    },
                ],
                "steps": [
                    {
                        "description": "Melanger",
                        "step_number": 1,
                        "dury": "2026-07-25T00:05:00Z",
                        "type": "prep",
                    },
                ],
            },
        ],
        "plannings": [
            {
                "name": "Semaine 1",
                "meals": [
                    {"recipe_id": 1, "type": "plat", "lunch": "midi", "dayofweek": "lundi"},
                ],
            },
        ],
    }
