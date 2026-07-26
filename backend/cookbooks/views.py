from django.db import models, transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from config.pagination import DefaultPagination

from .filters import CookbookFilter
from .models import Cookbook, SharedUserCookbook
from .permissions import IsCookbookAdmin
from .serializers import (
    CookbookSerializer,
    CookbookShareSerializer,
    CookbookUnshareSerializer,
    CookbookWriteSerializer,
)


@extend_schema_view(
    create=extend_schema(request=CookbookWriteSerializer, responses=CookbookSerializer),
    update=extend_schema(request=CookbookWriteSerializer, responses=CookbookSerializer),
    partial_update=extend_schema(request=CookbookWriteSerializer, responses=CookbookSerializer),
    share=extend_schema(
        request=CookbookShareSerializer,
        responses=CookbookSerializer,
        description=(
            "Grant or change one or more users' access to this cookbook in a single call. "
            "Accepts both `POST` (grant) and `PATCH` (change an existing role) - both do "
            "the same upsert, so either works for either case. Admin-only (the cookbook's "
            "creator, or staff) - see `cookbooks.permissions.IsCookbookAdmin`. Re-sharing "
            "with a user who already has access **updates their role** rather than "
            "creating a duplicate entry. Returns the cookbook with its up-to-date "
            "`shared_with` list."
        ),
        examples=[
            OpenApiExample(
                "Share with two users",
                summary="Grant editor and reader access",
                description="Give user 2 edit rights and user 3 read-only access at once.",
                value={
                    "shares": [
                        {"user": 2, "role": "editor"},
                        {"user": 3, "role": "reader"},
                    ]
                },
                request_only=True,
            ),
            OpenApiExample(
                "Cookbook after sharing",
                value={
                    "id": 1,
                    "name": "Recettes de famille",
                    "creator": {"id": 1, "username": "alice", "first_name": "Alice"},
                    "shared_with": [
                        {
                            "user": {"id": 2, "username": "bob", "first_name": "Bob"},
                            "role": "editor",
                            "created_at": "2026-07-25T10:00:00Z",
                            "updated_at": "2026-07-25T10:00:00Z",
                        },
                        {
                            "user": {"id": 3, "username": "carol", "first_name": "Carol"},
                            "role": "reader",
                            "created_at": "2026-07-25T10:00:00Z",
                            "updated_at": "2026-07-25T10:00:00Z",
                        },
                    ],
                    "recipes": [],
                    "plannings": [],
                    "created_at": "2026-07-20T09:00:00Z",
                    "updated_at": "2026-07-25T10:00:00Z",
                },
                response_only=True,
            ),
        ],
    ),
    unshare=extend_schema(
        request=CookbookUnshareSerializer,
        responses=CookbookSerializer,
        description=(
            "Revoke one or more users' access to this cookbook in a single call. "
            "Admin-only (the cookbook's creator, or staff) - see "
            "`cookbooks.permissions.IsCookbookAdmin`. Revoking a user who has no "
            "existing access is a no-op, not an error. Returns the cookbook with "
            "its up-to-date `shared_with` list."
        ),
        examples=[
            OpenApiExample(
                "Revoke two users",
                summary="Remove editor and reader access",
                description="Remove user 2's and user 3's access to the cookbook.",
                value={"users": [2, 3]},
                request_only=True,
            ),
        ],
    ),
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="name",
                type=OpenApiTypes.STR,
                description="Filtre par nom de cookbook (recherche partielle, insensible a la "
                "casse).",
                examples=[OpenApiExample("Exemple", value="Recettes de famille")],
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                description="Numero de page a retourner.",
                examples=[OpenApiExample("Exemple", value=1)],
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                description="Nombre de cookbooks par page (10 par defaut, 100 maximum).",
                examples=[OpenApiExample("Exemple", value=10)],
            ),
        ],
    ),
)
class CookbookViewSet(viewsets.ModelViewSet):
    """CRUD for cookbooks, plus ``share``/``unshare`` to grant/revoke access.

    ``share`` accepts both POST and PATCH (identical upsert behaviour -
    PATCH just reads better when changing an existing role). ``unshare`` is
    POST-only, kept as its own endpoint rather than a DELETE on ``share``
    since DELETE can't carry a documented JSON body in OpenAPI/
    drf-spectacular. Only cookbooks the caller created or was shared belong
    in ``get_queryset``, so a non-member gets a 404 rather than a 403 on
    retrieve. Renaming, deleting, sharing and unsharing a cookbook are
    admin-only (the cookbook's creator, or staff) - see
    ``cookbooks.permissions.IsCookbookAdmin``.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CookbookFilter
    pagination_class = DefaultPagination

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        user = self.request.user
        return (
            Cookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                models.Q(creator=user) | models.Q(shared_with__user=user)
            )
            .select_related("creator")
            .prefetch_related(
                "shared_with__user",
                "recipes__creator",
                "recipes__recipe_ingredients__ingredient",
                "recipes__recipe_tags__tag",
                "recipes__steps",
                "plannings__creator",
                "plannings__recipe_plannings__recipe__creator",
                "plannings__recipe_plannings__recipe__recipe_ingredients__ingredient",
                "plannings__recipe_plannings__recipe__recipe_tags__tag",
                "plannings__recipe_plannings__recipe__steps",
            )
            .distinct()
            .order_by("-updated_at")
        )

    def get_serializer_class(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.action in ("create", "update", "partial_update"):
            return CookbookWriteSerializer
        return CookbookSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy", "share", "unshare"):
            return [IsAuthenticated(), IsCookbookAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer: CookbookWriteSerializer) -> None:
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=["post", "patch"])
    def share(self, request: Request, pk=None) -> Response:
        cookbook = self.get_object()
        serializer = CookbookShareSerializer(data=request.data, context={"cookbook": cookbook})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            for item in serializer.validated_data["shares"]:  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
                SharedUserCookbook.objects.update_or_create(  # pyright: ignore[reportAttributeAccessIssue]
                    cookbook=cookbook, user=item["user"], defaults={"role": item["role"]}
                )

        # ``cookbook`` still carries the pre-share ``shared_with`` prefetch
        # cache from ``get_object()`` - re-fetch so the response is current.
        cookbook.refresh_from_db()
        return Response(CookbookSerializer(cookbook).data)

    @action(detail=True, methods=["post"])
    def unshare(self, request: Request, pk=None) -> Response:
        cookbook = self.get_object()
        serializer = CookbookUnshareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=cookbook,
            user__in=serializer.validated_data["users"],  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
        ).delete()

        cookbook.refresh_from_db()
        return Response(CookbookSerializer(cookbook).data)
