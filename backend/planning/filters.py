import django_filters

from .models import Planning


class PlanningFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    cookbook = django_filters.CharFilter(field_name="cookbook__name", lookup_expr="icontains")
    in_cookbook = django_filters.BooleanFilter(method="filter_in_cookbook")

    class Meta:
        model = Planning
        fields: list[str] = []

    def filter_in_cookbook(self, queryset, name, value):
        return queryset.filter(cookbook__isnull=not value)
