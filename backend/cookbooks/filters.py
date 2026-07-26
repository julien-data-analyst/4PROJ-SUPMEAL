import django_filters
from django.db.models import QuerySet

from .models import Cookbook


class CookbookFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    shared_with_me = django_filters.BooleanFilter(method="filter_shared_with_me")

    class Meta:
        model = Cookbook
        fields: list[str] = []

    def filter_shared_with_me(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """Cookbooks shared with the caller (not one they created themselves)."""
        user = self.request.user  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        if value:
            return queryset.filter(shared_with__user=user)
        return queryset.exclude(shared_with__user=user)
