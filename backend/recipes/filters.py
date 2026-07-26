import django_filters
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import FloatField, OuterRef, QuerySet, Subquery, Sum
from django.db.models.functions import Coalesce, ExtractHour, ExtractMinute, ExtractSecond

from .models import Recipe, Step

# ``Step.dury`` stores a step's duration as a fake timestamp: only its
# time-of-day part is meaningful (e.g. "00:05:00" means 5 minutes). This
# expression turns it back into a plain minute count.
_STEP_DURATION_MINUTES = (
    ExtractHour("dury") * 60 + ExtractMinute("dury") + ExtractSecond("dury") / 60.0
)


def _prep_minutes_subquery() -> Subquery:
    """Total step duration (in minutes) for a recipe, as a correlated subquery.

    Computed as a subquery rather than a plain ``annotate(Sum(...))`` on a
    joined relation so it isn't inflated by fan-out when the main query also
    joins other one-to-many relations (tags, ingredients, shared cookbook
    users).
    """
    return Subquery(
        Step.objects.filter(recipe=OuterRef("pk"))
        .values("recipe")
        .annotate(total=Sum(_STEP_DURATION_MINUTES, output_field=FloatField()))
        .values("total"),
        output_field=FloatField(),
    )


class RecipeFilter(django_filters.FilterSet):
    """Filters for the recipe list.

    ``tags``/``ingredients`` accept a comma-separated list of names and/or
    ids and require a recipe to have *all* of them (not just one). Prep time
    is derived from the sum of the recipe's step durations; cooking time is
    the plain ``cooking_duration`` field.
    """

    name = django_filters.CharFilter(method="filter_name")
    tags = django_filters.CharFilter(method="filter_tags")
    ingredients = django_filters.CharFilter(method="filter_ingredients")
    cookbook = django_filters.CharFilter(field_name="cookbook__name", lookup_expr="icontains")
    in_cookbook = django_filters.BooleanFilter(method="filter_in_cookbook")
    favorite = django_filters.BooleanFilter(method="filter_favorite")
    prep_time_min = django_filters.NumberFilter(method="filter_prep_time_min")
    prep_time_max = django_filters.NumberFilter(method="filter_prep_time_max")
    cooking_duration_min = django_filters.NumberFilter(
        field_name="cooking_duration", lookup_expr="gte"
    )
    cooking_duration_max = django_filters.NumberFilter(
        field_name="cooking_duration", lookup_expr="lte"
    )

    class Meta:
        model = Recipe
        fields: list[str] = []

    def filter_name(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        return queryset.annotate(search=SearchVector("title", config="french")).filter(
            search=SearchQuery(value, config="french")
        )

    @staticmethod
    def _tokens(value: str) -> list[str]:
        return [token.strip() for token in value.split(",") if token.strip()]

    def filter_tags(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        for token in self._tokens(value):
            if token.isdigit():
                queryset = queryset.filter(recipe_tags__tag__id=int(token))
            else:
                queryset = queryset.filter(recipe_tags__tag__name__iexact=token)
        return queryset

    def filter_ingredients(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        for token in self._tokens(value):
            if token.isdigit():
                queryset = queryset.filter(recipe_ingredients__ingredient__id=int(token))
            else:
                queryset = queryset.filter(recipe_ingredients__ingredient__name__iexact=token)
        return queryset

    def filter_in_cookbook(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        return queryset.filter(cookbook__isnull=not value)

    def filter_favorite(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        user = self.request.user  # pyright: ignore[reportAttributeAccessIssue]
        if value:
            return queryset.filter(favorited_by__user=user)
        return queryset.exclude(favorited_by__user=user)

    def filter_prep_time_min(self, queryset: QuerySet, name: str, value: float) -> QuerySet:
        return queryset.annotate(prep_minutes=Coalesce(_prep_minutes_subquery(), 0.0)).filter(
            prep_minutes__gte=value
        )

    def filter_prep_time_max(self, queryset: QuerySet, name: str, value: float) -> QuerySet:
        return queryset.annotate(prep_minutes=Coalesce(_prep_minutes_subquery(), 0.0)).filter(
            prep_minutes__lte=value
        )
