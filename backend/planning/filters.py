import django_filters
from django.db.models import QuerySet

from .models import Planning


class PlanningFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    cookbook = django_filters.CharFilter(field_name="cookbook__name", lookup_expr="icontains")
    in_cookbook = django_filters.BooleanFilter(method="filter_in_cookbook")
    shared_with_me = django_filters.BooleanFilter(method="filter_shared_with_me")

    class Meta:
        model = Planning
        fields: list[str] = []

    def filter_in_cookbook(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        return queryset.filter(cookbook__isnull=not value)

    def filter_shared_with_me(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """Plannings filed in a cookbook shared with the caller (not one they created)."""
        user = self.request.user  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        if value:
            return queryset.filter(cookbook__shared_with__user=user)
        return queryset.exclude(cookbook__shared_with__user=user)
