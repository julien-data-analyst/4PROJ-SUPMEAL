from django.db import models, transaction
from django.db.models import Exists, OuterRef
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
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from config.pagination import DefaultPagination
from cookbooks.permissions import CookbookItemPermission

from .export import RecipeExportSerializer, export_recipe, export_recipes
from .filters import RecipeFilter
from .imports import import_recipes
from .models import FavoriteRecipe, Ingredient, Recipe, Tag
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)

RECIPE_EXPORT_EXAMPLE = {
    "title": "Crepes",
    "image": None,
    "source": "https://example.com/crepes",
    "cooking_duration": "15.50",
    "created_at": "2026-07-20T09:00:00Z",
    "updated_at": "2026-07-20T09:00:00Z",
    "tags": [
        {"name": "Dessert", "type": "repas", "description": None},
    ],
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
}


@extend_schema_view(
    create=extend_schema(request=RecipeWriteSerializer, responses=RecipeSerializer),
    update=extend_schema(request=RecipeWriteSerializer, responses=RecipeSerializer),
    partial_update=extend_schema(request=RecipeWriteSerializer, responses=RecipeSerializer),
    export_detail=extend_schema(
        request=None,
        responses=RecipeExportSerializer,
        description=(
            "Export a single recipe (identified by `id` in the URL) as a portable JSON "
            "object: its own fields (`title`, `image`, `source`, `cooking_duration`, "
            "`created_at`, `updated_at`), its `tags` (by `name`, plus `type`/`description`), "
            "its `ingredients` (by `name`, plus `quantity`/`unity`/`person_numbers`) and its "
            "`steps` (every field except their internal `id`). Neither the recipe's `id`, "
            "`creator` nor `cookbook` are included, so the result can be re-imported as-is "
            "via `POST /api/recipes/import/` - it will land as a personal recipe "
            "(outside any cookbook) owned by whoever imports it. Any recipe you can read "
            "(your own, or one in a cookbook shared with you) can be exported this way."
        ),
        examples=[
            OpenApiExample(
                "Exported recipe",
                value=RECIPE_EXPORT_EXAMPLE,
                response_only=True,
            ),
        ],
    ),
    export_list=extend_schema(
        request=None,
        responses=RecipeExportSerializer(many=True),
        description=(
            "Export **your personal recipes** (recipes you created that aren't filed into "
            "any cookbook) as a JSON array, one portable object per recipe - see "
            "`GET /api/recipes/{id}/export/` for the shape of each object. The whole array "
            "can be re-imported as-is via `POST /api/recipes/import/`."
        ),
        examples=[
            OpenApiExample(
                "Exported personal recipes",
                value=[RECIPE_EXPORT_EXAMPLE],
                response_only=True,
            ),
        ],
    ),
    import_data=extend_schema(
        request=OpenApiTypes.OBJECT,
        responses=RecipeSerializer(many=True),
        description=(
            "Import one or more recipes from JSON previously produced by "
            "`GET /api/recipes/{id}/export/` or `GET /api/recipes/export/`. The request "
            "body may be **either a single recipe object or a JSON array of recipe "
            "objects** - both are accepted by this same endpoint. Every created recipe is "
            "always a personal recipe (`cookbook` is never set from the import, even if "
            "the exported recipe originally belonged to one) owned by the authenticated "
            "user. Ingredients/tags are matched by `name` (case-insensitive) and reused if "
            "they already exist in the catalogue, otherwise created; steps are always "
            "created fresh. The response is **always a JSON array** of the created recipes "
            "(in their full, nested `RecipeSerializer` shape), even when a single object "
            "was submitted. The import is all-or-nothing: if any item fails validation, "
            "nothing is created and a 400 is returned."
        ),
        examples=[
            OpenApiExample(
                "Import a single recipe",
                value=RECIPE_EXPORT_EXAMPLE,
                request_only=True,
            ),
            OpenApiExample(
                "Import a list of recipes",
                value=[RECIPE_EXPORT_EXAMPLE],
                request_only=True,
            ),
        ],
    ),
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="name",
                type=OpenApiTypes.STR,
                description="Correspondance partielle sur le titre de la recette.",
                examples=[OpenApiExample("Exemple", value="crepes")],
            ),
            OpenApiParameter(
                name="tags",
                type=OpenApiTypes.STR,
                description=(
                    "Liste de noms et/ou d'identifiants de tags separes par des virgules. "
                    "La recette doit porter TOUS les tags listes (ET logique)."
                ),
                examples=[OpenApiExample("Exemple", value="Vegetarien,Rapide")],
            ),
            OpenApiParameter(
                name="ingredients",
                type=OpenApiTypes.STR,
                description=(
                    "Liste de noms et/ou d'identifiants d'ingredients separes par des virgules. "
                    "La recette doit contenir TOUS les ingredients listes (ET logique)."
                ),
                examples=[OpenApiExample("Exemple", value="Farine,3")],
            ),
            OpenApiParameter(
                name="cookbook",
                type=OpenApiTypes.STR,
                description="Filtre par nom de cookbook (recherche partielle, insensible a la "
                "casse).",
                examples=[OpenApiExample("Exemple", value="Carnet de famille")],
            ),
            OpenApiParameter(
                name="in_cookbook",
                type=OpenApiTypes.BOOL,
                description=(
                    "`true` : uniquement les recettes rangees dans un cookbook. "
                    "`false` : uniquement les recettes autonomes (sans cookbook)."
                ),
                examples=[OpenApiExample("Exemple", value=True)],
            ),
            OpenApiParameter(
                name="planning",
                type=OpenApiTypes.STR,
                description="Filtre par nom de planning dans lequel la recette est "
                "programmee (recherche partielle, insensible a la casse).",
                examples=[OpenApiExample("Exemple", value="Semaine du 20 juillet")],
            ),
            OpenApiParameter(
                name="in_planning",
                type=OpenApiTypes.BOOL,
                description=(
                    "`true` : uniquement les recettes programmees dans au moins un "
                    "planning. `false` : uniquement celles qui ne le sont dans aucun."
                ),
                examples=[OpenApiExample("Exemple", value=True)],
            ),
            OpenApiParameter(
                name="favorite",
                type=OpenApiTypes.BOOL,
                description=(
                    "`true` : uniquement les recettes favorites de l'utilisateur courant. "
                    "`false` : uniquement celles qui ne le sont pas."
                ),
                examples=[OpenApiExample("Exemple", value=True)],
            ),
            OpenApiParameter(
                name="shared_with_me",
                type=OpenApiTypes.BOOL,
                description=(
                    "`true` : uniquement les recettes rangees dans un cookbook partage avec "
                    "l'utilisateur courant (dont il n'est pas le proprietaire). `false` : "
                    "exclut ces recettes."
                ),
                examples=[OpenApiExample("Exemple", value=True)],
            ),
            OpenApiParameter(
                name="prep_time_min",
                type=OpenApiTypes.NUMBER,
                description=(
                    "Temps de preparation minimal, en minutes (somme des durees des "
                    "etapes de la recette)."
                ),
                examples=[OpenApiExample("Exemple", value=10)],
            ),
            OpenApiParameter(
                name="prep_time_max",
                type=OpenApiTypes.NUMBER,
                description=(
                    "Temps de preparation maximal, en minutes (somme des durees des "
                    "etapes de la recette)."
                ),
                examples=[OpenApiExample("Exemple", value=30)],
            ),
            OpenApiParameter(
                name="cooking_duration_min",
                type=OpenApiTypes.NUMBER,
                description="Temps de cuisson minimal, en minutes (champ `cooking_duration`).",
                examples=[OpenApiExample("Exemple", value=5)],
            ),
            OpenApiParameter(
                name="cooking_duration_max",
                type=OpenApiTypes.NUMBER,
                description="Temps de cuisson maximal, en minutes (champ `cooking_duration`).",
                examples=[OpenApiExample("Exemple", value=60)],
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
                description="Nombre de recettes par page (10 par defaut, 100 maximum).",
                examples=[OpenApiExample("Exemple", value=10)],
            ),
        ],
    ),
)
class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD for recipes, including their ingredients, tags and steps.

    Reads use ``RecipeSerializer`` (nested, read-only). Writes use
    ``RecipeWriteSerializer``, which also creates/reuses the shared
    ``Ingredient``/``Tag`` rows and (re)creates the recipe's ``Step`` rows -
    see that serializer for the reuse rules. Responses always use the
    nested ``RecipeSerializer`` shape, including for create/update.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = DefaultPagination

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        user = self.request.user
        return (
            Recipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                models.Q(creator=user)  # pyright: ignore[reportOperatorIssue]
                | models.Q(cookbook__creator=user)
                | models.Q(cookbook__shared_with__user=user)
            )
            .select_related("creator", "cookbook")
            .prefetch_related(
                "recipe_ingredients__ingredient",
                "recipe_tags__tag",
                "steps",
                "recipe_plannings__planning",
            )
            .annotate(
                is_favorite=Exists(
                    FavoriteRecipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                        user=user, recipe=OuterRef("pk")
                    )
                )
            )
            .distinct()
            .order_by("-updated_at")
        )

    def get_serializer_class(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.action in ("create", "update", "partial_update"):
            return RecipeWriteSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action in ("retrieve", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), CookbookItemPermission()]
        return super().get_permissions()

    def perform_destroy(self, instance: Recipe) -> None:
        # Steps/ingredients/tags/favorites/recipe_plannings/messages are all
        # PROTECTed FKs to Recipe (no cascade), so they must be unlinked
        # explicitly before the recipe itself can go. `recipe_plannings` in
        # particular removes the recipe from every planning that scheduled
        # it - the plannings themselves are left otherwise untouched.
        with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
            instance.recipe_ingredients.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.recipe_tags.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.steps.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.favorited_by.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.recipe_plannings.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.messages.all().delete()  # pyright: ignore[reportAttributeAccessIssue]
            instance.delete()

    @action(detail=True, methods=["get"], url_path="export")
    def export_detail(self, request: Request, pk=None) -> Response:
        recipe = self.get_object()
        return Response(
            export_recipe(recipe),
            headers={"Content-Disposition": f'attachment; filename="recipe_{recipe.pk}.json"'},
        )

    @action(detail=False, methods=["get"], url_path="export")
    def export_list(self, request: Request) -> Response:
        recipes = Recipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            creator=request.user, cookbook__isnull=True
        ).prefetch_related("recipe_ingredients__ingredient", "recipe_tags__tag", "steps")
        return Response(
            export_recipes(recipes),
            headers={"Content-Disposition": 'attachment; filename="recipes_export.json"'},
        )

    @action(detail=False, methods=["post"], url_path="import")
    def import_data(self, request: Request) -> Response:
        recipes = import_recipes(request.data, request.user)
        return Response(
            RecipeSerializer(recipes, many=True, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post", "delete"])
    def favorite(self, request: Request, pk=None) -> Response:
        """Add (``POST``) or remove (``DELETE``) this recipe from the caller's favorites."""
        recipe = self.get_object()
        if request.method == "POST":
            _, created = FavoriteRecipe.objects.get_or_create(  # pyright: ignore[reportAttributeAccessIssue]
                user=request.user, recipe=recipe
            )
            return Response(status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        FavoriteRecipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            user=request.user, recipe=recipe
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
