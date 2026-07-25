"""Admin registrations for the ``planning`` app.

``RecipePlanning`` has a composite primary key, which the Django admin does
not support registering yet, so only ``Planning`` is exposed here.
"""

from django.contrib import admin

from .models import Planning

admin.site.register(Planning)
