from django.urls import path

from .views import CookbookMessageViewSet, RecipeMessageViewSet

# Nested under cookbooks/recipes rather than a DefaultRouter: messages only
# ever make sense scoped to a cookbook (and optionally one of its recipes),
# and there's no drf-nested-routers dependency in this project - see
# messaging/views.py for how cookbook_pk/recipe_pk are resolved.
cookbook_messages_list = CookbookMessageViewSet.as_view({"get": "list", "post": "create"})
cookbook_messages_detail = CookbookMessageViewSet.as_view({"get": "retrieve", "delete": "destroy"})
recipe_messages_list = RecipeMessageViewSet.as_view({"get": "list", "post": "create"})
recipe_messages_detail = RecipeMessageViewSet.as_view({"get": "retrieve", "delete": "destroy"})

urlpatterns = [
    path(
        "cookbooks/<int:cookbook_pk>/messages/",
        cookbook_messages_list,
        name="cookbook-message-list",
    ),
    path(
        "cookbooks/<int:cookbook_pk>/messages/<int:pk>/",
        cookbook_messages_detail,
        name="cookbook-message-detail",
    ),
    path(
        "cookbooks/<int:cookbook_pk>/recipes/<int:recipe_pk>/messages/",
        recipe_messages_list,
        name="recipe-message-list",
    ),
    path(
        "cookbooks/<int:cookbook_pk>/recipes/<int:recipe_pk>/messages/<int:pk>/",
        recipe_messages_detail,
        name="recipe-message-detail",
    ),
]
