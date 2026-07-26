from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile_icon",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


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
