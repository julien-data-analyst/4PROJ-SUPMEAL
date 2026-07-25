from django.db import models, transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from cookbooks.permissions import CookbookItemPermission

from .models import Planning
from .serializers import PlanningSerializer, PlanningWriteSerializer


@extend_schema_view(
    create=extend_schema(request=PlanningWriteSerializer, responses=PlanningSerializer),
    update=extend_schema(request=PlanningWriteSerializer, responses=PlanningSerializer),
    partial_update=extend_schema(request=PlanningWriteSerializer, responses=PlanningSerializer),
)
class PlanningViewSet(viewsets.ModelViewSet):
    """CRUD for weekly meal plannings, including their scheduled meals.

    Reads use ``PlanningSerializer`` (nested, read-only). Writes use
    ``PlanningWriteSerializer``, which (re)creates the planning's
    ``RecipePlanning`` rows - see that serializer for the scheduling rules.
    Responses always use the nested ``PlanningSerializer`` shape, including
    for create/update. A planning not filed into a cookbook is only
    visible/manageable by its creator; a planning filed into a cookbook is
    gated by the caller's role on that cookbook - see
    ``cookbooks.permissions.CookbookItemPermission``.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        user = self.request.user
        return (
            Planning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                models.Q(cookbook__isnull=True)  # pyright: ignore[reportOperatorIssue]
                | models.Q(creator=user)
                | models.Q(cookbook__creator=user)
                | models.Q(cookbook__shared_with__user=user)
            )
            .select_related("creator", "cookbook")
            .prefetch_related("recipe_plannings__recipe")
            .distinct()
        )

    def get_serializer_class(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.action in ("create", "update", "partial_update"):
            return PlanningWriteSerializer
        return PlanningSerializer

    def get_permissions(self):
        if self.action in ("retrieve", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), CookbookItemPermission()]
        return super().get_permissions()

    def perform_destroy(self, instance: Planning) -> None:
        # RecipePlanning is a PROTECTed FK to Planning (no cascade), so its
        # rows must be unlinked explicitly before the planning itself can go.
        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            instance.recipe_plannings.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.delete()
