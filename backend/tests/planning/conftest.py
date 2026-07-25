import pytest

from cookbooks.models import Cookbook, SharedUserCookbook
from planning.models import Planning, RecipePlanning
from recipes.models import Recipe
from tests.recipes.conftest import other_auth_client  # noqa: F401
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

#####################################-
# Fixtures for planning-related tests
#####################################-


@pytest.fixture
def entree_recipe(regular_user: User) -> Recipe:  # noqa: F811
    recipe = Recipe(title="Salade de tomates", creator=regular_user)
    recipe.save()
    return recipe


@pytest.fixture
def plat_recipe(regular_user: User) -> Recipe:  # noqa: F811
    recipe = Recipe(title="Poulet roti", creator=regular_user)
    recipe.save()
    return recipe


@pytest.fixture
def dessert_recipe(regular_user: User) -> Recipe:  # noqa: F811
    recipe = Recipe(title="Tarte aux pommes", creator=regular_user)
    recipe.save()
    return recipe


@pytest.fixture
def planning_payload(entree_recipe: Recipe, plat_recipe: Recipe, dessert_recipe: Recipe) -> dict:
    return {
        "name": "Semaine du 27 juillet",
        "meals": [
            {
                "recipe": entree_recipe.pk,
                "dayofweek": "lundi",
                "lunch": "midi",
                "type": "entree",
            },
            {
                "recipe": plat_recipe.pk,
                "dayofweek": "lundi",
                "lunch": "midi",
                "type": "plat",
            },
            {
                "recipe": dessert_recipe.pk,
                "dayofweek": "lundi",
                "lunch": "soir",
                "type": "dessert",
            },
        ],
    }


@pytest.fixture
def owned_planning(regular_user: User, entree_recipe: Recipe, plat_recipe: Recipe) -> Planning:  # noqa: F811
    """A planning owned by ``regular_user``, with two scheduled meals."""
    planning = Planning(name="Existing Planning", creator=regular_user)
    planning.save()

    RecipePlanning(
        planning=planning, recipe=entree_recipe, type="entree", lunch="midi", dayofweek="lundi"
    ).save()
    RecipePlanning(
        planning=planning, recipe=plat_recipe, type="plat", lunch="midi", dayofweek="lundi"
    ).save()

    return planning


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
    """A cookbook created by ``other_user`` and shared with ``regular_user``."""
    cookbook = Cookbook(name="Carnet de Bob", creator=other_user)
    cookbook.save()
    SharedUserCookbook(cookbook=cookbook, user=regular_user, role="editor").save()
    return cookbook


@pytest.fixture
def other_users_cookbook(other_user: User) -> Cookbook:  # noqa: F811
    cookbook = Cookbook(name="Carnet prive de Bob", creator=other_user)
    cookbook.save()
    return cookbook
