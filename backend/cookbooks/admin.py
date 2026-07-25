"""Admin registrations for the ``cookbooks`` app.

``SharedUserCookbook`` has a composite primary key, which the Django admin
does not support registering yet, so only ``Cookbook`` is exposed here.
"""

from django.contrib import admin

from .models import Cookbook

admin.site.register(Cookbook)
