from django.urls import path

from .views import (
    ClaimDetailView,
    ClaimListCreateView,
)


app_name = "claims"


urlpatterns = [
    path(
        "",
        ClaimListCreateView.as_view(),
        name="claim-list-create",
    ),
    path(
        "<int:pk>/",
        ClaimDetailView.as_view(),
        name="claim-detail",
    ),
]