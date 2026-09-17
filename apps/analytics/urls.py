from django.urls import path

from .views import SnowflakeHealthView


urlpatterns = [
    path(
        "snowflake/health/",
        SnowflakeHealthView.as_view(),
        name="snowflake-health",
    ),
]