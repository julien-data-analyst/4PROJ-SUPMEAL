from rest_framework.permissions import BasePermission


class IsSelfOrStaff(BasePermission):
    """Allows a user to modify their own account, or staff to modify any."""

    def has_object_permission(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, request, view, obj
    ) -> bool:
        return request.user.is_staff or obj == request.user
