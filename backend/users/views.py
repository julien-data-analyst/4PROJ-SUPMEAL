from datetime import UTC, datetime

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
)
from .permissions import IsSelfOrStaff
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    MicrosoftOAuthSerializer,
    UserRegisterSerializer,
    UserSerializer,
)


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


class ChangePasswordView(APIView):
    """View for changing the authenticated user's own password.

    Rejected for accounts that only have linked OAuth identities, since they
    have no local password to confirm/replace.
    """

    permission_classes = [IsAuthenticated]

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


class LogoutView(APIView):
    """Logs the authenticated user out by blacklisting their refresh and access tokens.

    Requires the refresh token in the request body; the access token used to
    authenticate the request is blacklisted too, so neither can be reused
    afterwards.
    """

    permission_classes = [IsAuthenticated]

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
