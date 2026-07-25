"""Admin registrations for the ``users`` app.

``User`` is registered with Django's built-in ``UserAdmin`` so it keeps the
familiar permissions/groups UI. ``OAuthUser`` uses the default admin form.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import OAuthUser, User

admin.site.register(User, UserAdmin)
admin.site.register(OAuthUser)
