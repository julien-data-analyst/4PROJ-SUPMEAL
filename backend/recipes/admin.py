"""Admin registrations for the ``recipes`` app.

``RecipeIngredient``, ``RecipeTag`` and ``UserPreference`` have composite
primary keys, which the Django admin does not support registering yet, so
only the "plain" models are exposed here.
"""

from django.contrib import admin

from .models import Ingredient, Recipe, Step, Tag

admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Recipe)
admin.site.register(Step)
