"""Microsoft OAuth (Azure AD / Entra ID) integration.

Exchanges an authorization code obtained by the frontend for a Microsoft
Graph access token, fetches the account's profile from Graph, and
provisions/links a local ``User`` + ``OAuthUser`` from it.
"""

import base64
import logging

import msal
import requests
from django.conf import settings
from django.db import transaction

from common.image_validation import ALLOWED_IMAGE_MIME_TYPES

from .models import OAuthUser, User

logger = logging.getLogger(__name__)

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


def _fetch_microsoft_photo_data_uri(access_token: str) -> str:
    """Downloads the account's Microsoft Graph profile photo, if any, as a data URI.

    ``GRAPH_PHOTO_URL`` used to be stored directly as ``profile_icon`` - but
    it's a live Graph endpoint gated behind the caller's own bearer token, so
    an ``<img src="...">`` pointed at it can't authenticate and always fails
    to load. Downloading the bytes once here and persisting them as a
    self-contained data URI (the same format manually-uploaded avatars use,
    see ``ChangeAvatarView``) makes it directly renderable instead.
    """
    response = requests.get(
        GRAPH_PHOTO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if not response.ok:
        if response.status_code != requests.codes.not_found:
            # 404 just means "no photo set" - anything else (401/403 from a
            # missing Graph permission grant, 5xx, ...) is worth surfacing,
            # since it silently produces the same empty result otherwise.
            logger.warning(
                "Microsoft Graph photo fetch failed with status %s: %s",
                response.status_code,
                response.text[:500],
            )
        return ""

    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    if content_type not in ALLOWED_IMAGE_MIME_TYPES:
        content_type = "image/jpeg"  # Graph always serves photos as JPEG.

    encoded = base64.b64encode(response.content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def _unique_username(base: str) -> str:
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base}{suffix}"
    return username


def get_or_create_user_from_microsoft(profile: dict, access_token: str) -> tuple[User, bool]:
    """Get or create a ``User`` + linked ``OAuthUser`` from a Microsoft Graph profile.

    Users are matched by email (case-insensitively, like every other email
    lookup in this app - see ``UserRegisterSerializer.validate_email`` and
    ``link_microsoft_account``), since ``OAuthUser`` has no external id field
    of its own. Returns ``(user, created)``.
    """
    email = profile.get("mail") or profile.get("userPrincipalName")
    if not email:
        raise MicrosoftOAuthError("Microsoft account has no email or userPrincipalName.")

    domain = email.split("@")[-1]
    profile_icon = _fetch_microsoft_photo_data_uri(access_token)

    with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
        user = User.objects.filter(email__iexact=email).first()
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
        elif profile_icon and user.profile_icon != profile_icon:
            # Keep an already-existing account's photo in sync with Microsoft's -
            # otherwise a stale/broken value set before this photo-fetching logic
            # existed (or before the account had a photo) would never refresh.
            user.profile_icon = profile_icon
            user.save(update_fields=["profile_icon"])

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


def link_microsoft_account(user: User, profile: dict, access_token: str) -> User:
    """Link a Microsoft identity to an already-authenticated ``user``.

    Unlike ``get_or_create_user_from_microsoft`` (used for login/registration,
    which matches-or-creates a user by email), this always targets the given
    ``user`` - used by the "connect my Microsoft account" settings action.
    Syncs ``user.email`` to the Microsoft profile's email (a future OAuth
    login must match this same user by email) and makes the local password
    unusable, since sign-in now only happens through Microsoft.
    """
    email = profile.get("mail") or profile.get("userPrincipalName")
    if not email:
        raise MicrosoftOAuthError("Microsoft account has no email or userPrincipalName.")

    if User.objects.exclude(pk=user.pk).filter(email__iexact=email).exists():
        raise MicrosoftOAuthError(
            "Ce compte Microsoft est déjà lié à un autre utilisateur. Veuillez utiliser un autre compte Microsoft ou contacter le support si vous pensez qu'il s'agit d'une erreur."
        )

    domain = email.split("@")[-1]
    profile_icon = _fetch_microsoft_photo_data_uri(access_token)

    with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
        user.email = email
        user.set_unusable_password()
        if profile_icon:
            user.profile_icon = profile_icon
        user.save()

        OAuthUser.objects.update_or_create(  # pyright: ignore[reportAttributeAccessIssue]
            provider="microsoft",
            user=user,
            defaults={
                "provider_url": settings.AZURE_AUTHORITY,
                "profile_icon": profile_icon,
                "domain": domain,
            },
        )

    return user
