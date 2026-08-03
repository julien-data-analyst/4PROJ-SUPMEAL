from django.db import transaction
from django.db.models import Q

from cookbooks.models import Cookbook, SharedUserCookbook
from messaging.models import Message
from planning.models import Planning, RecipePlanning
from recipes.models import FavoriteRecipe, Recipe, RecipeIngredient, RecipeTag, Step, UserPreference

from .models import OAuthUser, User


def delete_user_account(user: User) -> None:
    """Permanently deletes ``user``, unwinding every PROTECTed relation that
    would otherwise block the delete - directly, or via a cookbook the user
    created - in an order that never violates a PROTECT constraint.

    ``Ingredient``/``Tag`` are shared, reusable master data with no FK back
    to ``User`` and are intentionally left untouched, mirroring
    ``RecipeViewSet.perform_destroy``'s precedent of only clearing join
    tables, never the rows those joins point to.

    Note: this also removes any recipe/planning/message another user
    created inside a cookbook this user owns, and every message this user
    ever authored anywhere - both are unavoidable consequences of the
    all-``PROTECT`` schema, not bugs.
    """
    with transaction.atomic():  # pyright: ignore[reportGeneralTypeIssues]
        owned_cookbook_ids = list(
            Cookbook.objects.filter(creator=user).values_list("id", flat=True)  # pyright: ignore[reportAttributeAccessIssue]
        )
        recipe_ids = list(
            Recipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                Q(creator=user) | Q(cookbook_id__in=owned_cookbook_ids)
            ).values_list("id", flat=True)
        )
        planning_ids = list(
            Planning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
                Q(creator=user) | Q(cookbook_id__in=owned_cookbook_ids)
            ).values_list("id", flat=True)
        )

        Message.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            Q(author=user)  # pyright: ignore[reportOperatorIssue]
            | Q(cookbook_id__in=owned_cookbook_ids)
            | Q(recipe_id__in=recipe_ids)
        ).delete()
        RecipePlanning.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            Q(recipe_id__in=recipe_ids) | Q(planning_id__in=planning_ids)
        ).delete()
        RecipeIngredient.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            recipe_id__in=recipe_ids
        ).delete()
        RecipeTag.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            recipe_id__in=recipe_ids
        ).delete()
        Step.objects.filter(recipe_id__in=recipe_ids).delete()  # pyright: ignore[reportAttributeAccessIssue]
        FavoriteRecipe.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            Q(recipe_id__in=recipe_ids) | Q(user=user)
        ).delete()
        UserPreference.objects.filter(user=user).delete()  # pyright: ignore[reportAttributeAccessIssue]
        SharedUserCookbook.objects.filter(  # pyright: ignore[reportAttributeAccessIssue]
            Q(user=user) | Q(cookbook_id__in=owned_cookbook_ids)
        ).delete()

        Recipe.objects.filter(id__in=recipe_ids).delete()  # pyright: ignore[reportAttributeAccessIssue]
        Planning.objects.filter(id__in=planning_ids).delete()  # pyright: ignore[reportAttributeAccessIssue]
        Cookbook.objects.filter(id__in=owned_cookbook_ids).delete()  # pyright: ignore[reportAttributeAccessIssue]
        OAuthUser.objects.filter(user=user).delete()  # pyright: ignore[reportAttributeAccessIssue]

        user.delete()
