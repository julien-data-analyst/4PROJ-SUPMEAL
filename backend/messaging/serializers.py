from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    """Read-only representation of a message.

    ``cookbook``/``recipe`` are always derived from the URL the message was
    posted to (never from the request body) - see ``messaging.views``.
    """

    author = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "content", "canal", "author", "cookbook", "recipe", "created_at"]
        read_only_fields = fields


class MessageWriteSerializer(serializers.ModelSerializer):
    """Create a message. ``author``/``cookbook``/``recipe`` are set from the request/URL.

    There is no update variant: messages can only be posted or deleted.
    """

    class Meta:
        model = Message
        fields = ["id", "content", "canal"]
        read_only_fields = ["id"]

    def to_representation(self, instance: Message):  # pyright: ignore[reportIncompatibleMethodOverride]
        return MessageSerializer(instance, context=self.context).data
