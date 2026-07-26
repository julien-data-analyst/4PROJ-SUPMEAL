from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MicrosoftOAuthView,
    RegisterView,
    UserViewSet,
)

router = DefaultRouter()
router.register("", UserViewSet, basename="user")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="user-register"),
    path("login/", LoginView.as_view(), name="user-login"),
    path("logout/", LogoutView.as_view(), name="user-logout"),
    path("oauth/microsoft/", MicrosoftOAuthView.as_view(), name="oauth-microsoft"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("", include(router.urls)),
]
