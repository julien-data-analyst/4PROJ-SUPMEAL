from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CookbookViewSet

router = DefaultRouter()
router.register("cookbooks", CookbookViewSet, basename="cookbook")

urlpatterns = [
    path("", include(router.urls)),
]
