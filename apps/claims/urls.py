from django.urls import path

from .views import (
    ApproveClaimView,
    ClaimDetailView,
    ClaimEventListView,
    ClaimListCreateView,
    ClaimRequirementListView,
    ClaimSettlementDetailView,
    CloseClaimView,
    RejectClaimView,
    RequestAdditionalInformationView,
    ResumeReviewView,
    SettleClaimView,
    StartDocumentProcessingView,
    StartReviewView,
    StartSettlementView,
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

    # Workflow actions
    path(
        "<int:pk>/start-processing/",
        StartDocumentProcessingView.as_view(),
        name="claim-start-processing",
    ),
    path(
        "<int:pk>/start-review/",
        StartReviewView.as_view(),
        name="claim-start-review",
    ),
    path(
        "<int:pk>/request-information/",
        RequestAdditionalInformationView.as_view(),
        name="claim-request-information",
    ),
    path(
        "<int:pk>/resume-review/",
        ResumeReviewView.as_view(),
        name="claim-resume-review",
    ),
    path(
        "<int:pk>/approve/",
        ApproveClaimView.as_view(),
        name="claim-approve",
    ),
    path(
        "<int:pk>/reject/",
        RejectClaimView.as_view(),
        name="claim-reject",
    ),
    path(
        "<int:pk>/start-settlement/",
        StartSettlementView.as_view(),
        name="claim-start-settlement",
    ),
    path(
        "<int:pk>/settle/",
        SettleClaimView.as_view(),
        name="claim-settle",
    ),
    path(
        "<int:pk>/close/",
        CloseClaimView.as_view(),
        name="claim-close",
    ),

    # History / supporting information
    path(
        "<int:claim_id>/events/",
        ClaimEventListView.as_view(),
        name="claim-events",
    ),
    path(
        "<int:claim_id>/requirements/",
        ClaimRequirementListView.as_view(),
        name="claim-requirements",
    ),
    path(
        "<int:claim_id>/settlement/",
        ClaimSettlementDetailView.as_view(),
        name="claim-settlement",
    ),
]