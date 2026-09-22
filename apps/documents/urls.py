from django.urls import path

from .views import (
    ClaimDocumentDetailView,
    ClaimDocumentListCreateView,
)

app_name = "documents"

urlpatterns = [
    path(
        "claims/<int:claim_id>/documents/",
        ClaimDocumentListCreateView.as_view(),
        name="claim-document-list-create",
    ),
    path(
        "documents/<int:pk>/",
        ClaimDocumentDetailView.as_view(),
        name="claim-document-detail",
    ),
]