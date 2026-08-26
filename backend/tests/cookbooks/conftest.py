import pytest

from cookbooks.models import Cookbook, SharedUserCookbook
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
# Fixtures for cookbook-sharing tests
#####################################-


@pytest.fixture
def other_auth_client(api_client: APIClient, other_user: User) -> APIClient:  # noqa: F811
    api_client.force_authenticate(user=other_user)
    return api_client


@pytest.fixture
def stranger(make_user) -> User:  # noqa: F811
    """A third user, unrelated to any cookbook used in a given test."""
    return make_user(username="carol", email="carol@example.com", first_name="Carol", last_name="C")


@pytest.fixture
def stranger_client(api_client: APIClient, stranger: User) -> APIClient:  # noqa: F811
    api_client.force_authenticate(user=stranger)
    return api_client


@pytest.fixture
def owned_cookbook(regular_user: User) -> Cookbook:  # noqa: F811
    """A cookbook created by ``regular_user`` - they are its implicit admin."""
    cookbook = Cookbook(name="Mon carnet", creator=regular_user)
    cookbook.save()
    return cookbook


@pytest.fixture
def other_users_cookbook(other_user: User) -> Cookbook:  # noqa: F811
    """A cookbook created by ``other_user``, not shared with anyone yet."""
    cookbook = Cookbook(name="Carnet de Bob", creator=other_user)
    cookbook.save()
    return cookbook


def _share(cookbook: Cookbook, user: User, role: str) -> None:
    SharedUserCookbook(cookbook=cookbook, user=user, role=role).save()


@pytest.fixture
def cookbook_shared_as_creator(other_users_cookbook: Cookbook, regular_user: User) -> Cookbook:  # noqa: F811
    """``other_users_cookbook``, shared with ``regular_user`` at the "creator" role."""
    _share(other_users_cookbook, regular_user, SharedUserCookbook.Role.CREATOR)
    return other_users_cookbook


@pytest.fixture
def cookbook_shared_as_editor(other_users_cookbook: Cookbook, regular_user: User) -> Cookbook:  # noqa: F811
    """``other_users_cookbook``, shared with ``regular_user`` at the "editor" role."""
    _share(other_users_cookbook, regular_user, SharedUserCookbook.Role.EDITOR)
    return other_users_cookbook


@pytest.fixture
def cookbook_shared_as_commentator(other_users_cookbook: Cookbook, regular_user: User) -> Cookbook:  # noqa: F811
    """``other_users_cookbook``, shared with ``regular_user`` at the "commentator" role."""
    _share(other_users_cookbook, regular_user, SharedUserCookbook.Role.COMMENTATOR)
    return other_users_cookbook


@pytest.fixture
def cookbook_shared_as_reader(other_users_cookbook: Cookbook, regular_user: User) -> Cookbook:  # noqa: F811
    """``other_users_cookbook``, shared with ``regular_user`` at the "reader" role."""
    _share(other_users_cookbook, regular_user, SharedUserCookbook.Role.READER)
    return other_users_cookbook
