from rest_framework.permissions import SAFE_METHODS, BasePermission

from cookbooks.models import Cookbook, SharedUserCookbook
from cookbooks.permissions import ADMIN, get_role, has_rank


class CanAccessCookbookMessages(BasePermission):
    """Gates ``list``/``create`` on a cookbook's (or one of its recipes') messages.

    Every role on the cookbook - including ``reader`` - can read; posting a
    new message requires at least ``commentator``. Staff can always do
    both. Visibility of the cookbook itself (a stranger getting a 404
    rather than a 403) is handled upstream by ``view.get_cookbook()``, which
    only resolves cookbooks the caller is a member of - see
    ``cookbooks.permissions.CookbookItemPermission`` for the same pattern.
    """

    def has_permission(self, request, view) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        cookbook: Cookbook = view.get_cookbook()
        if request.user.is_staff:
            return True
        minimum = (
            SharedUserCookbook.Role.READER
            if request.method in SAFE_METHODS
            else SharedUserCookbook.Role.COMMENTATOR
        )
        return has_rank(request.user, cookbook, minimum)


class CanDeleteMessage(BasePermission):
    """Allows deleting a message to its own author, the cookbook's admin, or staff.

    There is deliberately no update permission/serializer anywhere in this
    app - messages can be posted and deleted, never edited.
    """

    def has_object_permission(self, request, view, obj) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        if request.user.is_staff or obj.author_id == request.user.id:
            return True
        return get_role(request.user, obj.cookbook) == ADMIN
