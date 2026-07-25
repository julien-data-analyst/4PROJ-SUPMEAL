from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from .models import Ingredient, Recipe, Tag
from .permissions import IsCreatorOrStaff
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)


@extend_schema_view(
    create=extend_schema(request=RecipeWriteSerializer, responses=RecipeSerializer),
    update=extend_schema(request=RecipeWriteSerializer, responses=RecipeSerializer),
    partial_update=extend_schema(request=RecipeWriteSerializer, responses=RecipeSerializer),
)
class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD for recipes, including their ingredients, tags and steps.

    Reads use ``RecipeSerializer`` (nested, read-only). Writes use
    ``RecipeWriteSerializer``, which also creates/reuses the shared
    ``Ingredient``/``Tag`` rows and (re)creates the recipe's ``Step`` rows -
    see that serializer for the reuse rules. Responses always use the
    nested ``RecipeSerializer`` shape, including for create/update.
    """

    queryset = Recipe.objects.select_related(  # pyright: ignore[reportAttributeAccessIssue]
        "creator", "cookbook"
    ).prefetch_related("recipe_ingredients__ingredient", "recipe_tags__tag", "steps")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.action in ("create", "update", "partial_update"):
            return RecipeWriteSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsCreatorOrStaff()]
        return super().get_permissions()

    def perform_destroy(self, instance: Recipe) -> None:
        # Steps/ingredients/tags are PROTECTed FKs to Recipe (no cascade), so
        # they must be unlinked explicitly before the recipe itself can go.
        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            instance.recipe_ingredients.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.recipe_tags.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.steps.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.delete()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse the shared ingredient catalogue (e.g. for search/autocomplete).

    Ingredients are created exclusively through the recipe endpoints - see
    ``RecipeWriteSerializer``.
    """

    queryset = Ingredient.objects.all()  # pyright: ignore[reportAttributeAccessIssue]
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name"]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse the shared tag catalogue (categories/sub-categories).

    Filter by ``type`` (the sub-category, e.g. "repas", "regime_alimentaire")
    to list the categories available for a given use case (e.g. planning).
    Tags are created exclusively through the recipe endpoints - see
    ``RecipeWriteSerializer``.
    """

    queryset = Tag.objects.all()  # pyright: ignore[reportAttributeAccessIssue]
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]
    filterset_fields = ["type"]
