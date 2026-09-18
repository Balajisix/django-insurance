from django.urls import path

from apps.analytics.views import (
    ClaimsAIAnalyticsView,
    ClaimsByPolicyTypeView,
    ClaimsByStatusView,
    ClaimsByTypeView,
    ClaimsDashboardView,
    ClaimsMonthlyTrendView,
    ClaimsOverviewView,
    ClaimsProcessingAnalyticsView,
    ClaimsSettlementAnalyticsView,
    CustomerClaimsAnalyticsView,
)

from .views import SnowflakeHealthView

app_name = "analytics"


urlpatterns = [
    path(
        "snowflake/health/",
        SnowflakeHealthView.as_view(),
        name="snowflake-health",
    ),
    path(
        "dashboard/",
        ClaimsDashboardView.as_view(),
        name="dashboard",
    ),

    path(
        "claims/overview/",
        ClaimsOverviewView.as_view(),
        name="claims-overview",
    ),

    path(
        "claims/by-type/",
        ClaimsByTypeView.as_view(),
        name="claims-by-type",
    ),

    path(
        "claims/by-status/",
        ClaimsByStatusView.as_view(),
        name="claims-by-status",
    ),

    path(
        "claims/monthly-trend/",
        ClaimsMonthlyTrendView.as_view(),
        name="claims-monthly-trend",
    ),

    path(
        "claims/by-policy-type/",
        ClaimsByPolicyTypeView.as_view(),
        name="claims-by-policy-type",
    ),

    path(
        "claims/processing/",
        ClaimsProcessingAnalyticsView.as_view(),
        name="claims-processing",
    ),

    path(
        "claims/settlement/",
        ClaimsSettlementAnalyticsView.as_view(),
        name="claims-settlement",
    ),

    path(
        "claims/ai/",
        ClaimsAIAnalyticsView.as_view(),
        name="claims-ai",
    ),

    path(
        "customers/claims/",
        CustomerClaimsAnalyticsView.as_view(),
        name="customer-claims",
    ),
]