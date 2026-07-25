from rest_framework.permissions import BasePermission


class IsCreatorOrStaff(BasePermission):
    """Allows a recipe's creator to modify it, or staff to modify any."""

    def has_object_permission(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, request, view, obj
    ) -> bool:
        return request.user.is_staff or obj.creator_id == request.user.id
