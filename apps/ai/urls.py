from django.urls import path

from .views import (
    DocumentExtractionDetailView,
    DocumentProcessingJobListView,
    DocumentProcessingStartView,
)


urlpatterns = [
    path(
        "documents/<int:document_id>/process/",
        DocumentProcessingStartView.as_view(),
        name="document-processing-start",
    ),
    path(
        "documents/<int:document_id>/processing-jobs/",
        DocumentProcessingJobListView.as_view(),
        name="document-processing-jobs",
    ),
    path(
        "documents/<int:document_id>/extraction/",
        DocumentExtractionDetailView.as_view(),
        name="document-extraction-detail",
    ),
]