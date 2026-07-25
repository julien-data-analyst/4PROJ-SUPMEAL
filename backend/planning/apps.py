from django.apps import AppConfig


class PlanningConfig(AppConfig):
    """Configuration for the ``planning`` app.

    Holds the ``Planning`` model and the ``RecipePlanning`` join table that
    schedules recipes within a plan.
    """

    default_auto_field = "django.db.models.BigAutoField"  # pyright: ignore[reportAssignmentType]
    name = "planning"
