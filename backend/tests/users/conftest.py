from typing import Any

import pytest
from rest_framework.response import Response
from rest_framework.test import APIClient as _APIClient

from users.models import User

##################################-
# Fixtures for user-related tests
##################################-


class APIClient(_APIClient):
    """Typed wrapper around DRF's APIClient.

    APIClient's multiple inheritance (APIRequestFactory, django's test Client)
    has no type annotations, which leads static analysis to resolve these
    methods' return type through the wrong branch of the MRO (a bare
    WSGIRequest instead of a Response). They do return Response at runtime.
    """

    def get(self, *args: Any, **kwargs: Any) -> Response:
        return super().get(*args, **kwargs)  # pyright: ignore[reportReturnType]

    def post(self, *args: Any, **kwargs: Any) -> Response:
        return super().post(*args, **kwargs)  # pyright: ignore[reportReturnType]

    def put(self, *args: Any, **kwargs: Any) -> Response:
        return super().put(*args, **kwargs)  # pyright: ignore[reportReturnType]

    def patch(self, *args: Any, **kwargs: Any) -> Response:
        return super().patch(*args, **kwargs)  # pyright: ignore[reportReturnType]

    def delete(self, *args: Any, **kwargs: Any) -> Response:
        return super().delete(*args, **kwargs)  # pyright: ignore[reportReturnType]


@pytest.fixture
def test_password() -> str:
    return "C0mplexPassw0rd!"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def make_user(db, test_password: str):
    def _make_user(*, password: str | None = None, **kwargs) -> User:
        kwargs.setdefault("username", "user")
        kwargs.setdefault("email", "user@example.com")
        user = User(**kwargs)
        user.set_password(password or test_password)
        user.save()
        return user

    return _make_user


@pytest.fixture
def regular_user(make_user) -> User:
    return make_user(username="alice", email="alice@example.com", first_name="Alice", last_name="A")


@pytest.fixture
def other_user(make_user) -> User:
    return make_user(username="bob", email="bob@example.com", first_name="Bob", last_name="B")


@pytest.fixture
def staff_user(make_user) -> User:
    return make_user(
        username="staffer",
        email="staffer@example.com",
        first_name="Staff",
        last_name="Er",
        is_staff=True,
    )


@pytest.fixture
def auth_client(api_client: APIClient, regular_user: User) -> APIClient:
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def staff_client(api_client: APIClient, staff_user: User) -> APIClient:
    api_client.force_authenticate(user=staff_user)
    return api_client


#################################
#################################
