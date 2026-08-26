import django_filters
from django.db.models import QuerySet

from .models import Cookbook, SharedUserCookbook


class CookbookFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    shared_with_me = django_filters.BooleanFilter(method="filter_shared_with_me")
    # The caller's own role on a cookbook shared with them - "admin" is
    # deliberately not a valid choice here since it's never stored (see
    # SharedUserCookbook.Role docstring): it's implicit for a cookbook's own
    # creator, who has no `shared_with` row at all, so filtering by any real
    # role already excludes personal (self-created) cookbooks on its own.
    role = django_filters.ChoiceFilter(
        choices=SharedUserCookbook.Role.choices, method="filter_role"
    )

    class Meta:
        model = Cookbook
        fields: list[str] = []

    def filter_shared_with_me(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """Cookbooks shared with the caller (not one they created themselves)."""
        user = self.request.user  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        if value:
            return queryset.filter(shared_with__user=user)
        return queryset.exclude(shared_with__user=user)

    def filter_role(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """Cookbooks shared with the caller at exactly this role."""
        user = self.request.user  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        return queryset.filter(shared_with__user=user, shared_with__role=value)
