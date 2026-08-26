"""Admin registrations for the ``messaging`` app."""

from django.contrib import admin

from .models import Message

admin.site.register(Message)
