import pytest
from django.urls import reverse
from rest_framework import status

from cookbooks.models import Cookbook
from planning.models import Planning
from tests.planning.conftest import APIClient
from users.models import User

pytestmark = pytest.mark.django_db


def _names(response) -> list[str]:
    return [planning["name"] for planning in response.data["results"]]


##########################-
# type
##########################-


def test_type_filter_matches_exact_planning_type(auth_client: APIClient, regular_user: User):
    """Test that ``?type=`` filters plannings by their exact type."""
    daily = Planning(name="Journee", creator=regular_user, type=Planning.Type.DAILY)
    daily.save()
    Planning(name="Semaine", creator=regular_user, type=Planning.Type.WEEKLY).save()
    url = reverse("planning-list")

    response = auth_client.get(url, {"type": Planning.Type.DAILY})

    assert _names(response) == [daily.name]


##########################-
# cookbook / in_cookbook
##########################-


def test_cookbook_filter_matches_cookbook_name(
    auth_client: APIClient, regular_user: User, owned_cookbook: Cookbook
):
    """Test that ``?cookbook=`` filters by (partial, case-insensitive) cookbook name."""
    filed = Planning(name="Planning range", creator=regular_user, cookbook=owned_cookbook)
    filed.save()
    Planning(name="Planning autonome", creator=regular_user).save()
    url = reverse("planning-list")

    response = auth_client.get(url, {"cookbook": str(owned_cookbook.name).lower()[:5]})

    assert _names(response) == [filed.name]


def test_in_cookbook_filter_true_and_false(
    auth_client: APIClient, regular_user: User, owned_cookbook: Cookbook
):
    """Test that ``?in_cookbook=`` filters plannings by whether they're filed in a cookbook."""
    filed = Planning(name="Planning range", creator=regular_user, cookbook=owned_cookbook)
    filed.save()
    standalone = Planning(name="Planning autonome", creator=regular_user)
    standalone.save()
    url = reverse("planning-list")

    response_true = auth_client.get(url, {"in_cookbook": "true"})
    response_false = auth_client.get(url, {"in_cookbook": "false"})

    assert _names(response_true) == [filed.name]
    assert _names(response_false) == [standalone.name]


##########################################-
# shared_with_me: cookbooks shared with the caller
##########################################-


def test_shared_with_me_filter_true_returns_only_plannings_from_cookbooks_shared_with_caller(
    auth_client: APIClient,
    regular_user: User,
    owned_cookbook: Cookbook,
    cookbook_shared_with_regular_user: Cookbook,
):
    """Test that ``?shared_with_me=true`` only returns plannings filed in a cookbook shared
    with the caller - not their own cookbooks, and not standalone plannings.
    """
    Planning(name="Dans mon carnet", creator=regular_user, cookbook=owned_cookbook).save()
    shared = Planning(
        name="Dans un carnet partage",
        creator=regular_user,
        cookbook=cookbook_shared_with_regular_user,
    )
    shared.save()
    Planning(name="Planning autonome", creator=regular_user).save()
    url = reverse("planning-list")

    response = auth_client.get(url, {"shared_with_me": "true"})

    assert _names(response) == [shared.name]


def test_shared_with_me_filter_false_excludes_plannings_from_cookbooks_shared_with_caller(
    auth_client: APIClient,
    regular_user: User,
    owned_cookbook: Cookbook,
    cookbook_shared_with_regular_user: Cookbook,
):
    """Test that ``?shared_with_me=false`` excludes plannings filed in a cookbook shared
    with the caller, keeping their own cookbooks and standalone plannings.
    """
    own = Planning(name="Dans mon carnet", creator=regular_user, cookbook=owned_cookbook)
    own.save()
    Planning(
        name="Dans un carnet partage",
        creator=regular_user,
        cookbook=cookbook_shared_with_regular_user,
    ).save()
    standalone = Planning(name="Planning autonome", creator=regular_user)
    standalone.save()
    url = reverse("planning-list")

    response = auth_client.get(url, {"shared_with_me": "false"})

    assert set(_names(response)) == {own.name, standalone.name}


def test_anonymous_user_cannot_list_plannings(api_client: APIClient):
    """Test that listing plannings requires authentication."""
    url = reverse("planning-list")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
