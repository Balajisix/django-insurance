from django.urls import path

from .views import (
    PolicyCoverageCreateView,
    PolicyDetailView,
    PolicyListCreateView,
)


app_name = "policies"


urlpatterns = [
    path(
        "",
        PolicyListCreateView.as_view(),
        name="policy-list-create",
    ),
    path(
        "<int:pk>/",
        PolicyDetailView.as_view(),
        name="policy-detail",
    ),
    path(
        "<int:pk>/coverages/",
        PolicyCoverageCreateView.as_view(),
        name="policy-coverage-create",
    ),
]