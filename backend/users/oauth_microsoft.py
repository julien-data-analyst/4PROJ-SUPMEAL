"""Microsoft OAuth (Azure AD / Entra ID) integration.

Exchanges an authorization code obtained by the frontend for a Microsoft
Graph access token, fetches the account's profile from Graph, and
provisions/links a local ``User`` + ``OAuthUser`` from it.
"""

import msal
import requests
from django.conf import settings
from django.db import transaction

from .models import OAuthUser, User

GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"
GRAPH_PHOTO_URL = "https://graph.microsoft.com/v1.0/me/photo/$value"
MICROSOFT_SCOPES = ["User.Read"]


class MicrosoftOAuthError(Exception):
    """Raised when the Microsoft code exchange or profile fetch fails."""


def _confidential_client() -> msal.ConfidentialClientApplication:
    return msal.ConfidentialClientApplication(
        client_id=settings.AZURE_CLIENT_ID,
        client_credential=settings.AZURE_CLIENT_SECRET,
        authority=settings.AZURE_AUTHORITY,
    )


def exchange_code_for_token(code: str) -> str:
    """Exchange an authorization code for a Microsoft Graph access token."""
    result = _confidential_client().acquire_token_by_authorization_code(
        code,
        scopes=MICROSOFT_SCOPES,
        redirect_uri=settings.AZURE_REDIRECT_URI,
    )
    if "access_token" not in result:
        error_description = result.get("error_description", result.get("error", "unknown error"))
        raise MicrosoftOAuthError(f"Microsoft token exchange failed: {error_description}")
    return result["access_token"]


def fetch_microsoft_profile(access_token: str) -> dict:
    """Fetch the authenticated account's profile from Microsoft Graph."""
    response = requests.get(
        GRAPH_ME_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=10
    )
    if not response.ok:
        raise MicrosoftOAuthError(f"Microsoft Graph profile fetch failed: {response.text}")
    return response.json()


def has_microsoft_photo(access_token: str) -> bool:
    """Check whether the Microsoft account has a profile photo set."""
    response = requests.get(
        GRAPH_PHOTO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
        stream=True,
    )
    response.close()
    return response.status_code == requests.codes.ok


def _unique_username(base: str) -> str:
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base}{suffix}"
    return username


def get_or_create_user_from_microsoft(profile: dict, access_token: str) -> tuple[User, bool]:
    """Get or create a ``User`` + linked ``OAuthUser`` from a Microsoft Graph profile.

    Users are matched by email, since ``OAuthUser`` has no external id field
    of its own. Returns ``(user, created)``.
    """
    email = profile.get("mail") or profile.get("userPrincipalName")
    if not email:
        raise MicrosoftOAuthError("Microsoft account has no email or userPrincipalName.")

    domain = email.split("@")[-1]
    profile_icon = GRAPH_PHOTO_URL if has_microsoft_photo(access_token) else ""

    with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
        user = User.objects.filter(email=email).first()
        created = False
        if user is None:
            base_username = (profile.get("userPrincipalName") or email).split("@")[0]
            user = User(
                username=_unique_username(base_username),
                first_name=profile.get("givenName", ""),
                last_name=profile.get("surname", ""),
                email=email,
                profile_icon=profile_icon,
            )
            user.set_unusable_password()
            user.save()
            created = True

        OAuthUser.objects.update_or_create(  # pyright: ignore[reportAttributeAccessIssue]
            provider="microsoft",
            user=user,
            defaults={
                "provider_url": settings.AZURE_AUTHORITY,
                "profile_icon": profile_icon,
                "domain": domain,
            },
        )

    return user, created
