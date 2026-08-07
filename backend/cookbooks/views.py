from django.db import models, transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from config.pagination import DefaultPagination

from .export import CookbookExportSerializer, export_cookbook, export_cookbooks
from .filters import CookbookFilter
from .imports import import_cookbooks
from .models import Cookbook, SharedUserCookbook
from .permissions import IsCookbookAdmin
from .serializers import (
    CookbookSerializer,
    CookbookShareSerializer,
    CookbookUnshareSerializer,
    CookbookWriteSerializer,
)

COOKBOOK_EXPORT_EXAMPLE = {
    "name": "Recettes de famille",
    "icon": None,
    "recipes": [
        {
            "id": 12,
            "title": "Crepes",
            "image": None,
            "source": "https://example.com/crepes",
            "cooking_duration": "15.50",
            "created_at": "2026-07-20T09:00:00Z",
            "updated_at": "2026-07-20T09:00:00Z",
            "tags": [{"name": "Dessert", "type": "repas", "description": None}],
            "ingredients": [
                {
                    "name": "Farine",
                    "image": None,
                    "quantity": "250.00",
                    "unity": "g",
                    "person_numbers": 4,
                },
            ],
            "steps": [
                {
                    "description": "Melanger farine et oeufs",
                    "step_number": 1,
                    "dury": "2026-07-25T00:05:00Z",
                    "type": "prep",
                },
            ],
        },
    ],
    "plannings": [
        {
            "name": "Semaine 1",
            "icon": None,
            "meals": [
                {"recipe_id": 12, "type": "plat", "lunch": "midi", "dayofweek": "lundi"},
            ],
        },
    ],
}


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
            "creating a duplicate entry. Each entry in `shares` identifies the user to "
            "share with by **either** `user` (their id) **or** `email` (their email "
            "address) - exactly one of the two must be given per entry. Returns the "
            "cookbook with its up-to-date `shared_with` list."
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
                "Share by email",
                summary="Grant access using an email address instead of a user id",
                description="Same as sharing by `user`, but identifying the user by `email`.",
                value={"shares": [{"email": "bob@example.com", "role": "editor"}]},
                request_only=True,
            ),
            OpenApiExample(
                "Cookbook after sharing",
                value={
                    "id": 1,
                    "name": "Recettes de famille",
                    "icon": "data:image/svg+xml;base64,...",
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
    export_detail=extend_schema(
        request=None,
        responses=CookbookExportSerializer,
        description=(
            "Export a single cookbook (identified by `id` in the URL) as a portable JSON "
            "object: its `name` and `icon`, the list of its `recipes` (each in the same "
            "shape as `GET /api/recipes/{id}/export/`, plus an export-local `id` used only "
            "to link it to plannings below) and the list of its `plannings` (each with its "
            "own `icon` and its scheduled `meals`, referencing a recipe via `recipe_id` "
            "matching one of the `id`s in `recipes[]` above - **not** a database id). "
            "Cookbook members (`shared_with`) are never included. A meal scheduling a "
            "recipe that isn't filed into this cookbook is silently omitted, since it has "
            "nothing to link to. The result can be re-imported as-is via "
            "`POST /api/cookbooks/import/`. Any cookbook you can read (your own, or one "
            "shared with you, at any role) can be exported this way."
        ),
        examples=[
            OpenApiExample(
                "Exported cookbook",
                value=COOKBOOK_EXPORT_EXAMPLE,
                response_only=True,
            ),
        ],
    ),
    export_list=extend_schema(
        request=None,
        responses=CookbookExportSerializer(many=True),
        description=(
            "Export **the cookbooks you created** (where you're the implicit admin) as a "
            "JSON array, one portable object per cookbook - see "
            "`GET /api/cookbooks/{id}/export/` for the shape of each object. Cookbooks only "
            "shared with you (not created by you) are not included. The whole array can be "
            "re-imported as-is via `POST /api/cookbooks/import/`. Pass `ids` (a "
            "comma-separated list of cookbook ids) to export only a subset of your cookbooks "
            "instead of all of them."
        ),
        parameters=[
            OpenApiParameter(
                name="ids",
                type=OpenApiTypes.STR,
                description=(
                    "Comma-separated list of cookbook ids to export (e.g. `1,2,3`). Only ids "
                    "among the cookbooks you created are matched; unknown or foreign ids are "
                    "silently ignored. Omit to export all of the cookbooks you created."
                ),
                required=False,
                examples=[OpenApiExample("Exemple", value="1,2,3")],
            ),
        ],
        examples=[
            OpenApiExample(
                "Exported cookbooks you created",
                value=[COOKBOOK_EXPORT_EXAMPLE],
                response_only=True,
            ),
        ],
    ),
    import_data=extend_schema(
        request=OpenApiTypes.OBJECT,
        responses=CookbookSerializer(many=True),
        description=(
            "Import one or more cookbooks from JSON previously produced by "
            "`GET /api/cookbooks/{id}/export/` or `GET /api/cookbooks/export/`. The request "
            "body may be **either a single cookbook object or a JSON array of cookbook "
            "objects** - both are accepted by this same endpoint. The authenticated user "
            "becomes the creator (and implicit admin) of every cookbook created; nested "
            "`recipes[]` are filed into the new cookbook (ingredients/tags matched by "
            "`name` and reused if they already exist, otherwise created; steps always "
            "created fresh) and nested `plannings[].meals[]` are rebuilt by resolving each "
            "`recipe_id` against the `id` carried by that same payload item's `recipes[]` - "
            "every `recipe_id` used in `meals[]` **must** match one of `recipes[].id`, or "
            "the whole import is rejected. No members are imported - only the creator has "
            "access to the new cookbook. The response is **always a JSON array** of the "
            "created cookbooks (in their full, nested `CookbookSerializer` shape), even "
            "when a single object was submitted. The import is all-or-nothing: if any item "
            "fails validation, nothing is created and a 400 is returned."
        ),
        examples=[
            OpenApiExample(
                "Import a single cookbook",
                value=COOKBOOK_EXPORT_EXAMPLE,
                request_only=True,
            ),
            OpenApiExample(
                "Import a list of cookbooks",
                value=[COOKBOOK_EXPORT_EXAMPLE],
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
                name="shared_with_me",
                type=OpenApiTypes.BOOL,
                description=(
                    "`true` : uniquement les cookbooks partages avec l'utilisateur courant "
                    "(dont il n'est pas le proprietaire). `false` : uniquement ses propres "
                    "cookbooks (crees par lui)."
                ),
                examples=[OpenApiExample("Exemple", value=True)],
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

    def perform_destroy(self, instance: Cookbook) -> None:
        # Recipe/Planning.cookbook, SharedUserCookbook.cookbook and
        # Message.cookbook are all PROTECTed FKs to Cookbook (no cascade).
        # Recipes/plannings filed in this cookbook survive as personal items
        # (their `cookbook` is just cleared) rather than being deleted along
        # with it; shares and messages only make sense in this cookbook's
        # context, so those rows are dropped.
        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            instance.recipes.update(cookbook=None)  # pyright: ignore[reportAttributeAccessIssue]
            instance.plannings.update(cookbook=None)  # pyright: ignore[reportAttributeAccessIssue]
            instance.shared_with.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.messages.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.delete()

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

    @action(detail=True, methods=["get"], url_path="export")
    def export_detail(self, request: Request, pk=None) -> Response:
        cookbook = self.get_object()
        return Response(
            export_cookbook(cookbook),
            headers={"Content-Disposition": f'attachment; filename="cookbook_{cookbook.pk}.json"'},
        )

    @action(detail=False, methods=["get"], url_path="export")
    def export_list(self, request: Request) -> Response:
        cookbooks = self.get_queryset().filter(creator=request.user)
        ids = request.query_params.get("ids")
        if isinstance(ids, str) and ids:
            id_list = [int(token) for token in ids.split(",") if token.strip().isdigit()]
            cookbooks = cookbooks.filter(pk__in=id_list)
        return Response(
            export_cookbooks(cookbooks),
            headers={"Content-Disposition": 'attachment; filename="cookbooks_export.json"'},
        )

    @action(detail=False, methods=["post"], url_path="import")
    def import_data(self, request: Request) -> Response:
        cookbooks = import_cookbooks(request.data, request.user)
        return Response(
            CookbookSerializer(cookbooks, many=True, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
