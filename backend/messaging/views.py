from django.db import models
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from config.pagination import DefaultPagination
from cookbooks.models import Cookbook
from planning.models import Planning
from recipes.models import Recipe

from .models import Message
from .permissions import CanAccessCookbookMessages, CanDeleteMessage
from .serializers import MessageSerializer, MessageWriteSerializer

COOKBOOK_PK_PARAMETER = OpenApiParameter(
    name="cookbook_pk",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.PATH,
    description="ID du cookbook dont on consulte/alimente le canal de messages.",
)
RECIPE_PK_PARAMETER = OpenApiParameter(
    name="recipe_pk",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.PATH,
    description=(
        "ID de la recette (doit appartenir au cookbook `cookbook_pk`) dont on "
        "consulte/alimente le canal de messages."
    ),
)
PLANNING_PK_PARAMETER = OpenApiParameter(
    name="planning_pk",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.PATH,
    description=(
        "ID du planning (doit appartenir au cookbook `cookbook_pk`) dont on "
        "consulte/alimente le canal de messages."
    ),
)


class BaseMessageViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Shared list/create/retrieve/destroy behaviour for both message channels.

    There is no update action: a posted message can never be edited, only
    deleted - see ``messaging.permissions.CanDeleteMessage``. ``author``,
    ``cookbook`` and (when relevant) ``recipe`` are always derived from the
    caller and the URL, never accepted from the request body.
    """

    permission_classes = [IsAuthenticated, CanAccessCookbookMessages]
    pagination_class = DefaultPagination

    def get_serializer_class(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.action == "create":
            return MessageWriteSerializer
        return MessageSerializer

    def get_permissions(self):
        permission_instances = [IsAuthenticated(), CanAccessCookbookMessages()]
        if self.action == "destroy":
            permission_instances.append(CanDeleteMessage())
        return permission_instances

    def get_cookbook(self) -> Cookbook:
        """The cookbook named by the URL, restricted to ones the caller can see.

        A cookbook the caller isn't a member of (and isn't staff) 404s here,
        rather than reaching the permission check - so a non-member can't
        even tell the cookbook exists (mirrors
        ``cookbooks.permissions.CookbookItemPermission``).
        """
        if not hasattr(self, "_cookbook"):
            user = self.request.user
            queryset = (
                Cookbook.objects.all()  # pyright: ignore[reportAttributeAccessIssue]
                if user.is_staff
                else Cookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                    models.Q(creator=user) | models.Q(shared_with__user=user)
                ).distinct()
            )
            self._cookbook = get_object_or_404(queryset, pk=self.kwargs["cookbook_pk"])
        return self._cookbook


@extend_schema_view(
    list=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER],
        tags=["Cookbook messages"],
        description=(
            "Liste les messages postes dans le canal global du cookbook (hors "
            "canal d'une recette precise). Accessible a tout membre du "
            "cookbook, y compris en lecture seule (`reader`)."
        ),
    ),
    create=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER],
        request=MessageWriteSerializer,
        responses=MessageSerializer,
        tags=["Cookbook messages"],
        description=(
            "Poste un message dans le canal global du cookbook. Necessite au "
            "moins le role `commentator` sur ce cookbook - un `reader` recoit "
            "un 403."
        ),
    ),
    retrieve=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER],
        tags=["Cookbook messages"],
        description="Recupere un message du canal global du cookbook par son id.",
    ),
    destroy=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER],
        tags=["Cookbook messages"],
        description=(
            "Supprime un message du canal global du cookbook. Reserve a "
            "l'auteur du message, a l'admin du cookbook (son createur) ou au "
            "staff. Il n'existe pas de route de modification : un message se "
            "supprime, il ne se modifie pas."
        ),
    ),
)
class CookbookMessageViewSet(BaseMessageViewSet):
    """Messages posted to a cookbook's global channel."""

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=self.get_cookbook(), recipe__isnull=True, planning__isnull=True
        ).select_related("author", "cookbook")

    def perform_create(self, serializer: MessageWriteSerializer) -> None:
        serializer.save(
            author=self.request.user, cookbook=self.get_cookbook(), recipe=None, planning=None
        )


@extend_schema_view(
    list=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER, RECIPE_PK_PARAMETER],
        tags=["Recipe messages"],
        description=(
            "Liste les messages postes dans le canal de la recette "
            "`recipe_pk` (au sein du cookbook `cookbook_pk`). Accessible a "
            "tout membre du cookbook, y compris en lecture seule (`reader`)."
        ),
    ),
    create=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER, RECIPE_PK_PARAMETER],
        request=MessageWriteSerializer,
        responses=MessageSerializer,
        tags=["Recipe messages"],
        description=(
            "Poste un message dans le canal de la recette `recipe_pk`. "
            "Necessite au moins le role `commentator` sur le cookbook "
            "`cookbook_pk` - un `reader` recoit un 403."
        ),
    ),
    retrieve=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER, RECIPE_PK_PARAMETER],
        tags=["Recipe messages"],
        description="Recupere un message du canal de la recette par son id.",
    ),
    destroy=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER, RECIPE_PK_PARAMETER],
        tags=["Recipe messages"],
        description=(
            "Supprime un message du canal de la recette. Reserve a l'auteur "
            "du message, a l'admin du cookbook (son createur) ou au staff. "
            "Il n'existe pas de route de modification : un message se "
            "supprime, il ne se modifie pas."
        ),
    ),
)
class RecipeMessageViewSet(BaseMessageViewSet):
    """Messages posted to a specific recipe's channel, within a cookbook.

    The recipe must belong to the cookbook named in the URL (``recipe.cookbook_id
    == cookbook_pk``) - otherwise ``get_recipe()`` 404s, so a recipe/cookbook
    id mismatch can't be used to leak or misfile a message.
    """

    def get_recipe(self) -> Recipe:
        if not hasattr(self, "_recipe"):
            self._recipe = get_object_or_404(
                Recipe,  # pyright: ignore[reportAttributeAccessIssue]
                pk=self.kwargs["recipe_pk"],
                cookbook=self.get_cookbook(),
            )
        return self._recipe

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=self.get_cookbook(), recipe=self.get_recipe()
        ).select_related("author", "cookbook", "recipe")

    def perform_create(self, serializer: MessageWriteSerializer) -> None:
        serializer.save(
            author=self.request.user, cookbook=self.get_cookbook(), recipe=self.get_recipe()
        )


@extend_schema_view(
    list=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER, PLANNING_PK_PARAMETER],
        tags=["Planning messages"],
        description=(
            "Liste les messages postes dans le canal du planning "
            "`planning_pk` (au sein du cookbook `cookbook_pk`). Accessible a "
            "tout membre du cookbook, y compris en lecture seule (`reader`)."
        ),
    ),
    create=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER, PLANNING_PK_PARAMETER],
        request=MessageWriteSerializer,
        responses=MessageSerializer,
        tags=["Planning messages"],
        description=(
            "Poste un message dans le canal du planning `planning_pk`. "
            "Necessite au moins le role `commentator` sur le cookbook "
            "`cookbook_pk` - un `reader` recoit un 403."
        ),
    ),
    retrieve=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER, PLANNING_PK_PARAMETER],
        tags=["Planning messages"],
        description="Recupere un message du canal du planning par son id.",
    ),
    destroy=extend_schema(
        parameters=[COOKBOOK_PK_PARAMETER, PLANNING_PK_PARAMETER],
        tags=["Planning messages"],
        description=(
            "Supprime un message du canal du planning. Reserve a l'auteur "
            "du message, a l'admin du cookbook (son createur) ou au staff. "
            "Il n'existe pas de route de modification : un message se "
            "supprime, il ne se modifie pas."
        ),
    ),
)
class PlanningMessageViewSet(BaseMessageViewSet):
    """Messages posted to a specific planning's channel, within a cookbook.

    The planning must belong to the cookbook named in the URL
    (``planning.cookbook_id == cookbook_pk``) - otherwise ``get_planning()``
    404s, mirroring ``RecipeMessageViewSet.get_recipe()``.
    """

    def get_planning(self) -> Planning:
        if not hasattr(self, "_planning"):
            self._planning = get_object_or_404(
                Planning,  # pyright: ignore[reportAttributeAccessIssue]
                pk=self.kwargs["planning_pk"],
                cookbook=self.get_cookbook(),
            )
        return self._planning

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            cookbook=self.get_cookbook(), planning=self.get_planning()
        ).select_related("author", "cookbook", "planning")

    def perform_create(self, serializer: MessageWriteSerializer) -> None:
        serializer.save(
            author=self.request.user, cookbook=self.get_cookbook(), planning=self.get_planning()
        )
