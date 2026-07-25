from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Planning
from .permissions import IsCreatorOrStaff
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
    for create/update.
    """

    queryset = Planning.objects.select_related(  # pyright: ignore[reportAttributeAccessIssue]
        "creator", "cookbook"
    ).prefetch_related("recipe_plannings__recipe")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.action in ("create", "update", "partial_update"):
            return PlanningWriteSerializer
        return PlanningSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsCreatorOrStaff()]
        return super().get_permissions()

    def perform_destroy(self, instance: Planning) -> None:
        # RecipePlanning is a PROTECTed FK to Planning (no cascade), so its
        # rows must be unlinked explicitly before the planning itself can go.
        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            instance.recipe_plannings.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.delete()
