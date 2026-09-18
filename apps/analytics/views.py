from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.permissions import IsAnalyticsUser
from apps.analytics.repository import (
    AnalyticsRepositoryError,
)
from apps.analytics.serializers import (
    AIAnalyticsSerializer,
    ClaimOverviewSerializer,
    ClaimStatusAnalyticsSerializer,
    ClaimTypeAnalyticsSerializer,
    ClaimsDashboardSerializer,
    CustomerClaimsAnalyticsSerializer,
    MonthlyClaimTrendSerializer,
    PolicyTypeAnalyticsSerializer,
    ProcessingAnalyticsSerializer,
    SettlementAnalyticsSerializer,
)
from apps.analytics.services import AnalyticsService

from .snowflake.client import SnowflakeClient


class SnowflakeHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            client = SnowflakeClient()

            (
                account,
                user,
                role,
                warehouse,
                database,
                schema,
            ) = client.test_connection()

            return Response(
                {
                    "status": "CONNECTED",
                    "snowflake": {
                        "account": account,
                        "user": user,
                        "role": role,
                        "warehouse": warehouse,
                        "database": database,
                        "schema": schema,
                    },
                }
            )

        except Exception as exc:
            return Response(
                {
                    "status": "FAILED",
                    "error": str(exc),
                },
                status=500,
            )

class AnalyticsBaseView(APIView):

    authentication_classes = [
        TokenAuthentication,
    ]

    permission_classes = [
        IsAuthenticated,
        IsAnalyticsUser,
    ]

    def get_service(self):
        return AnalyticsService()

    def handle_repository_error(
        self,
        exc,
    ):
        return Response(
            {
                "detail": (
                    "Analytics data is temporarily unavailable."
                ),
                "code": "ANALYTICS_UNAVAILABLE",
            },
            status=503,
        )


class ClaimsOverviewView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_overview()
            )

            serializer = ClaimOverviewSerializer(
                result
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )


class ClaimsByTypeView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_claims_by_type()
            )

            serializer = ClaimTypeAnalyticsSerializer(
                result,
                many=True,
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )


class ClaimsByStatusView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_claims_by_status()
            )

            serializer = ClaimStatusAnalyticsSerializer(
                result,
                many=True,
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )


class ClaimsMonthlyTrendView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_monthly_trend()
            )

            serializer = MonthlyClaimTrendSerializer(
                result,
                many=True,
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )


class ClaimsByPolicyTypeView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_claims_by_policy_type()
            )

            serializer = PolicyTypeAnalyticsSerializer(
                result,
                many=True,
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )


class ClaimsProcessingAnalyticsView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_processing_analytics()
            )

            serializer = ProcessingAnalyticsSerializer(
                result,
                many=True,
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )


class ClaimsSettlementAnalyticsView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_settlement_analytics()
            )

            serializer = SettlementAnalyticsSerializer(
                result,
                many=True,
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )


class ClaimsAIAnalyticsView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_ai_analytics()
            )

            serializer = AIAnalyticsSerializer(
                result,
                many=True,
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )


class CustomerClaimsAnalyticsView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_customer_claims()
            )

            serializer = CustomerClaimsAnalyticsSerializer(
                result,
                many=True,
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )


class ClaimsDashboardView(
    AnalyticsBaseView
):

    def get(self, request):

        try:

            result = (
                self.get_service()
                .get_dashboard()
            )

            serializer = ClaimsDashboardSerializer(
                result
            )

            return Response(
                serializer.data
            )

        except AnalyticsRepositoryError as exc:

            return self.handle_repository_error(
                exc
            )