from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Cookbook, SharedUserCookbook

ADMIN = "admin"

# Higher rank = more rights. "admin" is never stored (see SharedUserCookbook.Role
# docstring) - it's implicit for the cookbook's own creator.
ROLE_RANK = {
    SharedUserCookbook.Role.READER: 1,
    SharedUserCookbook.Role.COMMENTATOR: 2,
    SharedUserCookbook.Role.EDITOR: 3,
    SharedUserCookbook.Role.CREATOR: 4,
    ADMIN: 5,
}


def get_role(user, cookbook: Cookbook) -> str | None:
    """The caller's role on ``cookbook``, or ``None`` if they have no access."""
    if cookbook.creator_id == user.id:  # pyright: ignore[reportAttributeAccessIssue]
        return ADMIN
    shared = cookbook.shared_with.filter(user=user).first()  # pyright: ignore[reportAttributeAccessIssue]
    return shared.role if shared else None


def has_rank(user, cookbook: Cookbook, minimum: str) -> bool:
    role = get_role(user, cookbook)
    if role is None:
        return False
    return ROLE_RANK[role] >= ROLE_RANK[minimum]


class IsCookbookAdmin(BasePermission):
    """Allows only the cookbook's creator (its implicit admin), or staff."""

    def has_object_permission(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, request, view, obj: Cookbook
    ) -> bool:
        return request.user.is_staff or get_role(request.user, obj) == ADMIN


class CookbookItemPermission(BasePermission):
    """Permission for objects that carry a ``creator`` and an optional ``cookbook``
    (``Recipe``, ``Planning``): the object's own creator always has full rights;
    otherwise rights are derived from the caller's role on ``obj.cookbook``, when set.
    An object with no cookbook (``cookbook=None``) is only ever manageable by its
    creator - it isn't part of any shared collection.
    """

    def has_object_permission(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, request, view, obj
    ) -> bool:
        if request.user.is_staff or obj.creator_id == request.user.id:
            return True
        if obj.cookbook_id is None:
            return False
        if request.method in SAFE_METHODS:
            minimum = SharedUserCookbook.Role.READER
        elif request.method == "DELETE":
            minimum = SharedUserCookbook.Role.CREATOR
        else:
            minimum = SharedUserCookbook.Role.EDITOR
        return has_rank(request.user, obj.cookbook, minimum)
