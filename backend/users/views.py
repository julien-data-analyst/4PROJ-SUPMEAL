from datetime import UTC, datetime

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken, Token

from .models import User
from .oauth_microsoft import (
    MicrosoftOAuthError,
    exchange_code_for_token,
    fetch_microsoft_profile,
    get_or_create_user_from_microsoft,
    link_microsoft_account,
)
from .permissions import IsSelfOrStaff
from .serializers import (
    ChangeAvatarSerializer,
    ChangeEmailSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    MicrosoftOAuthSerializer,
    UserRegisterSerializer,
    UserSerializer,
)
from .services import delete_user_account

AUTH_TOKENS_EXAMPLE = {
    "user": {
        "id": 42,
        "username": "jane.doe",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "profile_icon": "",
        "created_at": "2026-07-25T10:00:00Z",
        "updated_at": "2026-07-25T10:00:00Z",
    },
    "access": "<jwt access token>",
    "refresh": "<jwt refresh token>",
}


def _tokens_for(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _blacklist_access_token(token: Token) -> None:
    """Blacklists an access token, mirroring what ``RefreshToken.blacklist()`` does.

    Access tokens aren't tracked as ``OutstandingToken`` by Simple JWT (only
    refresh tokens are), so the row has to be created here before it can be
    blacklisted. Paired with ``BlacklistAwareJWTAuthentication``, this makes
    the current access token unusable immediately instead of staying valid
    until it naturally expires.
    """

    outstanding, _created = OutstandingToken.objects.get_or_create(  # pyright: ignore[reportAttributeAccessIssue]
        jti=token["jti"],
        defaults={
            "token": str(token),
            "created_at": datetime.fromtimestamp(float(token["iat"]), tz=UTC),
            "expires_at": datetime.fromtimestamp(float(token["exp"]), tz=UTC),
            "user_id": int(token["user_id"]),
        },
    )
    BlacklistedToken.objects.get_or_create(  # pyright: ignore[reportAttributeAccessIssue]
        token=outstanding
    )


class RegisterView(generics.CreateAPIView):
    """View for user registration."""

    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"user": UserSerializer(user).data, **_tokens_for(user)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """View for user login."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses=OpenApiTypes.OBJECT,
        description=(
            "Authenticates a user with their email and password and returns a fresh JWT "
            "pair. Fails with `400 Bad Request` if the email is unknown, the password is "
            "wrong, or the account is disabled - the same generic error message is used "
            "for all three so a caller can't tell which one applies. Accounts created "
            "through an OAuth provider only (no local password set) will also be rejected "
            "here, since `authenticate()` cannot validate a password that doesn't exist."
        ),
        examples=[
            OpenApiExample(
                "Login response",
                value=AUTH_TOKENS_EXAMPLE,
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data[  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
            "user"
        ]
        return Response({"user": UserSerializer(user).data, **_tokens_for(user)})


class MicrosoftOAuthView(APIView):
    """Exchanges a Microsoft authorization code for a Graph profile and logs the user in."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=MicrosoftOAuthSerializer,
        responses=OpenApiTypes.OBJECT,
        description=(
            "Completes the Microsoft (Entra ID) OAuth login: exchanges the authorization "
            "`code` obtained from Microsoft for a Graph access token (server-side only, "
            "using `AZURE_CLIENT_SECRET`), fetches the user's profile and photo presence "
            "from Microsoft Graph, then gets-or-creates the matching `User` (matched by "
            'email) and its linked `OAuthUser(provider="microsoft")` row. Returns the '
            "same `{ user, access, refresh }` envelope as `/api/users/login/`. See "
            "`docs/oauth.md` for the full end-to-end flow, including how a frontend "
            "should obtain `code` in the first place. Fails with `400 Bad Request` if "
            "`code` is missing, Microsoft rejects the exchange (expired/already-used "
            "code, wrong `redirect_uri`, revoked consent, ...), or the Graph profile has "
            "neither `mail` nor `userPrincipalName` to key the account on."
        ),
        examples=[
            OpenApiExample(
                "Microsoft login response",
                value=AUTH_TOKENS_EXAMPLE,
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = MicrosoftOAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            code = serializer.validated_data[  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
                "code"
            ]
            access_token = exchange_code_for_token(code)
            profile = fetch_microsoft_profile(access_token)
            user, _created = get_or_create_user_from_microsoft(profile, access_token)
        except MicrosoftOAuthError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"user": UserSerializer(user).data, **_tokens_for(user)})


class LinkMicrosoftOAuthView(APIView):
    """Links the authenticated user's own account to a Microsoft identity.

    Unlike ``MicrosoftOAuthView`` (login/registration, ``AllowAny``), this
    always targets ``request.user`` rather than matching/creating a user by
    email - it's the "connect my Microsoft account" settings action. The
    account's email is synced to the Microsoft profile's, and its local
    password is made unusable: sign-in only works through Microsoft from
    then on.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=MicrosoftOAuthSerializer,
        responses=OpenApiTypes.OBJECT,
        description=(
            "Links the authenticated user's account to a Microsoft identity: exchanges "
            "the authorization `code` for a Graph access token, fetches the profile, then "
            "syncs the account's email to the Microsoft profile's email and makes its local "
            "password unusable - **the account can only sign in via Microsoft OAuth "
            "afterwards**. Fails with `400 Bad Request` if `code` is missing, the exchange "
            "fails, the profile has no email, or that email already belongs to a *different* "
            "account."
        ),
        examples=[
            OpenApiExample(
                "Microsoft account linked",
                value={
                    "user": AUTH_TOKENS_EXAMPLE["user"],
                    "detail": (
                        "Microsoft account linked successfully. You can only sign in with "
                        "Microsoft from now on."
                    ),
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = MicrosoftOAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            code = serializer.validated_data[  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
                "code"
            ]
            access_token = exchange_code_for_token(code)
            profile = fetch_microsoft_profile(access_token)
            user = link_microsoft_account(request.user, profile, access_token)
        except MicrosoftOAuthError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "user": UserSerializer(user).data,
                "detail": (
                    "Microsoft account linked successfully. You can only sign in with "
                    "Microsoft from now on."
                ),
            }
        )


class ChangePasswordView(APIView):
    """View for changing the authenticated user's own password.

    Rejected for accounts that only have linked OAuth identities, since they
    have no local password to confirm/replace.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses=OpenApiTypes.OBJECT,
        description=(
            "Changes the authenticated user's own password. Requires the `current_password` "
            "to be confirmed and the `new_password` to pass Django's configured password "
            "validators (minimum length, not too common, not entirely numeric, not too "
            "similar to the user's own attributes). Fails with `400 Bad Request` if "
            "`current_password` doesn't match, `new_password` fails validation, or the "
            "account only has linked OAuth identities (no local password to replace). "
            "Existing access/refresh tokens are **not** revoked by this call - pair it "
            "with `POST /api/users/logout/` if the other sessions should be invalidated "
            "too."
        ),
        examples=[
            OpenApiExample(
                "Password changed",
                value={"detail": "Password updated successfully."},
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        request.user.set_password(
            serializer.validated_data[  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
                "new_password"
            ]
        )
        request.user.save()
        return Response({"detail": "Password updated successfully."})


class ChangeEmailView(APIView):
    """View for changing the authenticated user's own email address.

    An OAuth-only account may also change its email here, provided it sets
    a `new_password` in the same request (enforced by ``ChangeEmailSerializer``)
    - since Microsoft OAuth login matches users by email, changing it would
    otherwise desync the two silently. Doing so also unlinks every OAuth
    identity from the account (deleted, not just left stale) - the account
    now signs in locally, with the password it was just given.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangeEmailSerializer,
        responses=OpenApiTypes.OBJECT,
        description=(
            "Changes the authenticated user's own email address. If the account only has "
            "linked OAuth identities, `new_password` is also required in the same request: "
            "the account's password is set to it and every linked `OAuthUser` is deleted, "
            "so the account becomes local-only (sign-in via OAuth will no longer reach it). "
            "Fails with `400 Bad Request` if `new_email` is already used by another account, "
            "or an OAuth account omits `new_password`/gives one failing validation."
        ),
        examples=[
            OpenApiExample(
                "Email changed (local account)",
                value={
                    "detail": "Email updated successfully.",
                    "email": "new@example.com",
                    "oauth_unlinked": False,
                },
                response_only=True,
            ),
            OpenApiExample(
                "Email changed (was OAuth-only, now local)",
                value={
                    "detail": "Email updated successfully.",
                    "email": "new@example.com",
                    "oauth_unlinked": True,
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = ChangeEmailSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        was_oauth = user.oauth_accounts.exists()  # pyright: ignore[reportAttributeAccessIssue]

        user.email = data["new_email"]  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
        if was_oauth:
            user.set_password(
                data["new_password"]  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
            )
        user.save()

        if was_oauth:
            user.oauth_accounts.all().delete()  # pyright: ignore[reportAttributeAccessIssue]

        return Response(
            {
                "detail": "Email updated successfully.",
                "email": user.email,
                "oauth_unlinked": was_oauth,
            }
        )


class ChangeAvatarView(APIView):
    """View for changing the authenticated user's own avatar.

    ``avatar`` is a base64 image data URI (PNG, JPEG or SVG only - see
    ``common.image_validation.validate_image_data_uri``), stored directly on
    ``profile_icon``. Available to OAuth accounts too - this simply
    overrides whatever avatar was originally synced from the provider.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangeAvatarSerializer,
        responses=OpenApiTypes.OBJECT,
        description=(
            "Changes the authenticated user's own avatar, including for OAuth accounts "
            "(overrides the avatar synced from the provider). `avatar` must be a base64 "
            "data URI for a PNG, JPEG or SVG image. Fails with `400 Bad Request` if the "
            "image type isn't allowed or the data is malformed."
        ),
        examples=[
            OpenApiExample(
                "Avatar changed",
                value={
                    "detail": "Avatar updated successfully.",
                    "profile_icon": "data:image/png;base64,...",
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = ChangeAvatarSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        request.user.profile_icon = serializer.validated_data[  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
            "avatar"
        ]
        request.user.save()
        return Response(
            {"detail": "Avatar updated successfully.", "profile_icon": request.user.profile_icon}
        )


class LogoutView(APIView):
    """Logs the authenticated user out by blacklisting their refresh and access tokens.

    Requires the refresh token in the request body; the access token used to
    authenticate the request is blacklisted too, so neither can be reused
    afterwards.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses=OpenApiTypes.OBJECT,
        description=(
            "Logs the authenticated user out by blacklisting both their `refresh` token "
            "(given in the request body) and the `access` token used to authenticate this "
            "very request (read from the `Authorization: Bearer` header) - see "
            "`users.authentication.BlacklistAwareJWTAuthentication` for how the access "
            "token half is enforced on subsequent requests. Both tokens become unusable "
            "immediately: the refresh token can no longer be exchanged via "
            "`/api/users/token/refresh/`, and the access token is rejected on any "
            "authenticated route. Fails with `400 Bad Request` if `refresh` is missing, "
            "malformed/expired, already blacklisted, or doesn't belong to the "
            "authenticated user (e.g. someone else's refresh token)."
        ),
        examples=[
            OpenApiExample(
                "Logged out",
                value={"detail": "Logged out successfully."},
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = RefreshToken(
                serializer.validated_data[  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
                    "refresh"
                ]
            )
        except TokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if str(refresh_token["user_id"]) != str(request.user.id):
            return Response(
                {"detail": "Refresh token does not belong to the authenticated user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh_token.blacklist()
        _blacklist_access_token(request.auth)

        return Response({"detail": "Logged out successfully."})


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet for managing users."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), IsAdminUser()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsSelfOrStaff()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def me(self, request: Request) -> Response:
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def perform_destroy(self, instance: User) -> None:
        delete_user_account(instance)
