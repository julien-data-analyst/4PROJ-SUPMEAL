from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from common.image_validation import validate_image_data_uri

from .models import User


class UserSerializer(serializers.ModelSerializer):
    is_oauth = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile_icon",
            "is_oauth",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "profile_icon", "created_at", "updated_at"]

    def get_is_oauth(self, obj: User) -> bool:
        return obj.oauth_accounts.exists()  # pyright: ignore[reportAttributeAccessIssue]


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile_icon",
            "password",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value: str) -> str:
        # `User.email` is `unique=True`, so ModelSerializer already rejects
        # an exact duplicate - but that DB-level uniqueness (and the
        # auto-generated validator built from it) is case-sensitive, which
        # would let "alice@example.com" and "Alice@Example.com" both
        # register. Match ChangeEmailSerializer's case-insensitive check so
        # the same address can't be used twice under either flow.
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MicrosoftOAuthSerializer(serializers.Serializer):
    code = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate(self, attrs: dict) -> dict:
        user = self.context["request"].user

        if user.oauth_accounts.exists():
            raise serializers.ValidationError("OAuth accounts cannot change their password here.")

        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError("Current password is incorrect.")

        return attrs


class ChangeEmailSerializer(serializers.Serializer):
    """Changes the caller's email.

    An OAuth-only account (no usable local password) may also change its
    email, but must set ``new_password`` in the same request: Microsoft
    OAuth login matches users by email, so changing it here breaks that
    match - the account needs a local password to still be reachable
    afterwards. See ``ChangeEmailView`` for what happens to its OAuth link.
    """

    new_email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        user = self.context["request"].user
        is_oauth = user.oauth_accounts.exists()
        new_password = attrs.get("new_password") or ""

        if is_oauth:
            if not new_password:
                raise serializers.ValidationError(
                    {
                        "new_password": (
                            "A local password is required when changing the email of an "
                            "OAuth-only account - you will no longer be able to sign in via "
                            "OAuth afterwards."
                        )
                    }
                )
            validate_password(new_password)

        if User.objects.exclude(pk=user.pk).filter(email__iexact=attrs["new_email"]).exists():
            raise serializers.ValidationError({"new_email": "This email is already in use."})

        return attrs


class ChangeAvatarSerializer(serializers.Serializer):
    """Changes the caller's avatar - OAuth accounts included, overriding
    whatever avatar was originally synced from the provider."""

    avatar = serializers.CharField(validators=[validate_image_data_uri])


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs: dict) -> dict:
        try:
            user_obj = User.objects.get(email=attrs["email"])
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        user = authenticate(
            request=self.context.get("request"),
            username=user_obj.username,
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        attrs["user"] = user
        return attrs


class SafeTokenRefreshSerializer(TokenRefreshSerializer):
    """``TokenRefreshSerializer`` that rejects tokens for since-deleted users cleanly.

    The stock serializer looks up the user for the token's ``user_id`` claim
    but never catches ``User.DoesNotExist`` - if the account was removed (or
    the database was reset) after the refresh token was issued, that raw
    lookup bubbles up as an unhandled 500 instead of a normal 401. This
    treats that case the same as any other invalid token.
    """

    def validate(self, attrs: dict) -> dict:
        try:
            return super().validate(attrs)
        except User.DoesNotExist:
            raise InvalidToken("No account found for this token.")
