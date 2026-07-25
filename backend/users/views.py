from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

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
    MicrosoftOAuthSerializer,
    UserRegisterSerializer,
    UserSerializer,
)


def _tokens_for(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


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
