import pytest
from django.utils import timezone

from cookbooks.models import Cookbook, SharedUserCookbook
from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Step, Tag
from tests.users.conftest import (  # noqa: F401
    APIClient,
    api_client,
    auth_client,
    make_user,
    other_user,
    regular_user,
    test_password,
)
from users.models import User

####################################-
# Fixtures for recipe-related tests
####################################-


@pytest.fixture
def other_auth_client(api_client: APIClient, other_user: User) -> APIClient:  # noqa: F811
    api_client.force_authenticate(user=other_user)
    return api_client


@pytest.fixture
def recipe_payload() -> dict:
    return {
        "title": "Crepes",
        "source": "https://example.com/crepes",
        "cooking_duration": "15.50",
        "ingredients": [
            {"name": "Farine", "quantity": "250.00", "unity": "g", "person_numbers": 4},
            {"name": "Oeuf", "quantity": "3.00", "unity": "unite", "person_numbers": 4},
        ],
        "tags": [
            {"name": "Dessert", "type": "repas"},
            {"name": "Vegetarien", "type": "regime_alimentaire", "description": "Sans viande"},
        ],
        "steps": [
            {
                "description": "Melanger farine et oeufs",
                "step_number": 1,
                "dury": "2026-07-25T00:05:00Z",
                "type": "prep",
            },
            {
                "description": "Cuire la pate",
                "step_number": 2,
                "dury": "2026-07-25T00:10:00Z",
                "type": "cook",
            },
        ],
    }


@pytest.fixture
def owned_recipe(regular_user: User) -> Recipe:  # noqa: F811
    """A recipe owned by ``regular_user``, with one ingredient, one tag and one step."""
    recipe = Recipe(title="Existing Recipe", creator=regular_user)
    recipe.save()

    ingredient = Ingredient(name="Sel")
    ingredient.save()
    RecipeIngredient(
        recipe=recipe, ingredient=ingredient, quantity=5, unity="g", person_numbers=2
    ).save()

    tag = Tag(name="Plat", type="repas")
    tag.save()
    RecipeTag(recipe=recipe, tag=tag).save()

    Step(
        recipe=recipe,
        description="Cuire a feu doux",
        step_number=1,
        dury=timezone.now(),
        type="cook",
    ).save()

    return recipe


@pytest.fixture
def owned_cookbook(regular_user: User) -> Cookbook:  # noqa: F811
    cookbook = Cookbook(name="Mon carnet", creator=regular_user)
    cookbook.save()
    return cookbook


@pytest.fixture
def cookbook_shared_with_regular_user(
    other_user: User,  # noqa: F811
    regular_user: User,  # noqa: F811
) -> Cookbook:
    """A cookbook created by ``other_user`` and shared with ``regular_user`` at
    the "creator" role, i.e. with enough rights to file new recipes into it.
    """
    cookbook = Cookbook(name="Carnet de Bob", creator=other_user)
    cookbook.save()
    SharedUserCookbook(cookbook=cookbook, user=regular_user, role="creator").save()
    return cookbook


@pytest.fixture
def other_users_cookbook(other_user: User) -> Cookbook:  # noqa: F811
    cookbook = Cookbook(name="Carnet prive de Bob", creator=other_user)
    cookbook.save()
    return cookbook
