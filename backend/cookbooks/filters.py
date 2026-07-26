import django_filters

from .models import Cookbook


class CookbookFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Cookbook
        fields: list[str] = []
