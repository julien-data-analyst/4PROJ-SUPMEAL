from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Configuration for the ``recipes`` app.

    Holds ``Recipe`` and its supporting models: ``Ingredient``, ``Tag``,
    ``Step`` and the ``RecipeIngredient``/``RecipeTag``/``UserPreference``
    join tables.
    """

    default_auto_field = "django.db.models.BigAutoField"  # pyright: ignore[reportAssignmentType]
    name = "recipes"
