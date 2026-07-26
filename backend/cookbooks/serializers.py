from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from planning.serializers import PlanningSerializer
from recipes.serializers import RecipeSerializer
from users.models import User
from users.serializers import UserSerializer

from .models import Cookbook, SharedUserCookbook


class SharedUserCookbookSerializer(serializers.ModelSerializer):
    """Read-only representation of one user's share on a cookbook."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = SharedUserCookbook
        fields = ["user", "role", "created_at", "updated_at"]
        read_only_fields = fields


class CookbookSerializer(serializers.ModelSerializer):
    """Read-only representation of a cookbook: who it's shared with and its contents.

    ``recipes``/``plannings`` list every ``Recipe``/``Planning`` filed into this
    cookbook (via their ``cookbook`` FK) - not just the ones the caller created.
    """

    creator = UserSerializer(read_only=True)
    shared_with = SharedUserCookbookSerializer(many=True, read_only=True)
    recipes = RecipeSerializer(many=True, read_only=True)
    plannings = PlanningSerializer(many=True, read_only=True)

    class Meta:
        model = Cookbook
        fields = [
            "id",
            "name",
            "creator",
            "shared_with",
            "recipes",
            "plannings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CookbookWriteSerializer(serializers.ModelSerializer):
    """Create/update a cookbook. ``creator`` is set from the request, not the payload."""

    class Meta:
        model = Cookbook
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def to_representation(self, instance: Cookbook):  # pyright: ignore[reportIncompatibleMethodOverride]
        return CookbookSerializer(instance, context=self.context).data


class ShareItemSerializer(serializers.Serializer):
    """One ``{user, role}`` or ``{email, role}`` entry of a share request.

    The user to share with can be identified either by their ``id`` (``user``)
    or by their ``email`` address - exactly one of the two must be given.
    """

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        help_text="ID of the user to grant access to. Provide this or `email`, not both.",
    )
    email = serializers.EmailField(
        required=False,
        help_text="Email address of the user to grant access to. Provide this or `user`, not both.",
    )
    role = serializers.ChoiceField(
        choices=SharedUserCookbook.Role.choices,
        help_text=(
            "Permission level to grant. From most to least permissive: `creator` "
            "(create, edit and delete recipes/plannings), `editor` (edit existing "
            "recipes/plannings only), `commentator` (read-only, for commenting) or "
            "`reader` (read-only). There is no `admin` role here - the cookbook's "
            "creator is always its implicit admin and can't be added to `shares`."
        ),
    )

    def validate(self, attrs: dict) -> dict:
        user = attrs.get("user")
        email = attrs.get("email")
        if bool(user) == bool(email):
            raise serializers.ValidationError(
                "Provide exactly one of `user` (id) or `email`, not both or neither."
            )
        if email:
            try:
                attrs["user"] = User.objects.get(email__iexact=email)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    {"email": "No user found with this email address."}
                )
            del attrs["email"]
        return attrs


class CookbookShareSerializer(serializers.Serializer):
    """Write-only payload for sharing a cookbook with one or more users."""

    shares = ShareItemSerializer(
        many=True,
        help_text="One or more {user, role} entries to grant or update in a single call.",
    )

    def validate_shares(self, shares: list[dict]) -> list[dict]:
        cookbook: Cookbook = self.context["cookbook"]
        if any(
            item["user"].id == cookbook.creator_id  # pyright: ignore[reportAttributeAccessIssue]
            for item in shares
        ):
            raise serializers.ValidationError(
                "Cannot share a cookbook with its own creator (already admin)."
            )
        return shares


class CookbookUnshareSerializer(serializers.Serializer):
    """Write-only payload for revoking one or more users' access to a cookbook."""

    users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        help_text=(
            "IDs of the users whose access to this cookbook should be revoked. "
            "A user with no existing access is silently ignored."
        ),
    )
