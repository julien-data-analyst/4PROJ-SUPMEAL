import pytest

from cookbooks.models import Cookbook
from messaging.models import Message
from recipes.models import Recipe
from tests.cookbooks.conftest import (  # noqa: F401
    cookbook_shared_as_commentator,
    cookbook_shared_as_creator,
    cookbook_shared_as_editor,
    cookbook_shared_as_reader,
    other_auth_client,
    other_users_cookbook,
    owned_cookbook,
    stranger,
    stranger_client,
)
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

######################################-
# Fixtures for messaging-related tests
######################################-


@pytest.fixture
def owned_recipe(regular_user: User, owned_cookbook: Cookbook) -> Recipe:  # noqa: F811
    """A recipe filed into ``owned_cookbook``, created by its owner."""
    recipe = Recipe(title="Recette existante", creator=regular_user, cookbook=owned_cookbook)
    recipe.save()
    return recipe


@pytest.fixture
def recipe_in_other_users_cookbook(other_user: User, other_users_cookbook: Cookbook) -> Recipe:  # noqa: F811
    """A recipe filed into ``other_users_cookbook``, created by its owner."""
    recipe = Recipe(title="Recette de Bob", creator=other_user, cookbook=other_users_cookbook)
    recipe.save()
    return recipe


@pytest.fixture
def message_payload() -> dict:
    return {"content": "Miam, ca a l'air delicieux !", "canal": "general"}


@pytest.fixture
def owned_cookbook_message(regular_user: User, owned_cookbook: Cookbook) -> Message:  # noqa: F811
    """A message posted by ``regular_user`` in ``owned_cookbook``'s global channel."""
    message = Message(
        content="Bienvenue dans ce carnet !",
        canal="general",
        author=regular_user,
        cookbook=owned_cookbook,
    )
    message.save()
    return message


@pytest.fixture
def owned_recipe_message(
    regular_user: User,  # noqa: F811
    owned_cookbook: Cookbook,  # noqa: F811
    owned_recipe: Recipe,
) -> Message:
    """A message posted by ``regular_user`` in ``owned_recipe``'s channel."""
    message = Message(
        content="Cette recette est excellente",
        canal="general",
        author=regular_user,
        cookbook=owned_cookbook,
        recipe=owned_recipe,
    )
    message.save()
    return message
