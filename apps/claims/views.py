from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.policies.models import Policy
from apps.users.models import UserRole
from apps.users.permissions import IsClaimsStaff

from .models import (
    Claim,
    ClaimDocumentRequirement,
    ClaimEvent,
    ClaimSettlement,
)
from .serializers import (
    ClaimApprovalSerializer,
    ClaimCreateSerializer,
    ClaimDocumentRequirementSerializer,
    ClaimEventSerializer,
    ClaimInformationRequestSerializer,
    ClaimRejectionSerializer,
    ClaimSerializer,
    ClaimSettlementSerializer,
    ClaimSettlementResponseSerializer,
    ClaimActionCommentSerializer,
)
from .services import ClaimService
from .workflow import ClaimWorkflowService


class ClaimListCreateView(
    generics.ListCreateAPIView
):
    """
    GET  /api/v1/claims/
    POST /api/v1/claims/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    queryset = (
        Claim.objects
        .select_related(
            "policy",
            "policy__customer",
        )
        .all()
    )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClaimCreateSerializer

        return ClaimSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            return queryset.filter(
                policy__customer__user=user
            )

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        if request.user.role == UserRole.CUSTOMER:
            policy_exists = (
                Policy.objects.filter(
                    id=data["policy_id"],
                    customer__user=request.user,
                ).exists()
            )

            if not policy_exists:
                return Response(
                    {
                        "error": {
                            "code": (
                                "POLICY_NOT_FOUND"
                            ),
                            "message": (
                                "Policy not found."
                            ),
                        }
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        claim = ClaimService.submit_claim(
            policy_id=data["policy_id"],
            claim_type=data["claim_type"],
            incident_date=data["incident_date"],
            incident_description=data[
                "incident_description"
            ],
            estimated_loss=data[
                "estimated_loss"
            ],
        )

        response_serializer = ClaimSerializer(
            claim
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ClaimDetailView(
    generics.RetrieveAPIView
):
    """
    GET /api/v1/claims/{id}/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    queryset = (
        Claim.objects
        .select_related(
            "policy",
            "policy__customer",
        )
        .all()
    )

    serializer_class = ClaimSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            return queryset.filter(
                policy__customer__user=user
            )

        return queryset


class ClaimWorkflowActionView(
    APIView
):
    """
    Generic workflow action endpoint handler.

    Every workflow transition (start processing/review,
    request information, resume, approve, reject, start
    settlement, settle, close) is a staff-only action —
    a customer can submit a claim and track its status,
    but cannot move it through the workflow themselves.
    """

    permission_classes = [
        IsAuthenticated,
        IsClaimsStaff,
    ]

    def get_claim(self, pk):
        try:
            return Claim.objects.get(
                id=pk
            )
        except Claim.DoesNotExist:
            return None


class StartDocumentProcessingView(
    ClaimWorkflowActionView
):
    def post(self, request, pk):
        claim = self.get_claim(pk)

        if claim is None:
            return Response(
                {
                    "error": {
                        "code": "CLAIM_NOT_FOUND",
                        "message": "Claim not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        event = (
            ClaimWorkflowService
            .start_document_processing(
                claim=claim,
                actor=request.user,
            )
        )

        return Response(
            ClaimEventSerializer(event).data,
            status=status.HTTP_200_OK,
        )


class StartReviewView(
    ClaimWorkflowActionView
):
    def post(self, request, pk):
        claim = self.get_claim(pk)

        if claim is None:
            return Response(
                {
                    "error": {
                        "code": "CLAIM_NOT_FOUND",
                        "message": "Claim not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        event = (
            ClaimWorkflowService
            .start_review(
                claim=claim,
                actor=request.user,
            )
        )

        return Response(
            ClaimEventSerializer(event).data,
            status=status.HTTP_200_OK,
        )


class RequestAdditionalInformationView(
    ClaimWorkflowActionView
):
    def post(self, request, pk):
        claim = self.get_claim(pk)

        if claim is None:
            return Response(
                {
                    "error": {
                        "code": "CLAIM_NOT_FOUND",
                        "message": "Claim not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            ClaimInformationRequestSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        event = (
            ClaimWorkflowService
            .request_additional_information(
                claim=claim,
                actor=request.user,
                comment=serializer.validated_data[
                    "comment"
                ],
            )
        )

        return Response(
            ClaimEventSerializer(event).data,
            status=status.HTTP_200_OK,
        )


class ResumeReviewView(
    ClaimWorkflowActionView
):
    def post(self, request, pk):
        claim = self.get_claim(pk)

        if claim is None:
            return Response(
                {
                    "error": {
                        "code": "CLAIM_NOT_FOUND",
                        "message": "Claim not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        event = (
            ClaimWorkflowService
            .resume_review(
                claim=claim,
                actor=request.user,
            )
        )

        return Response(
            ClaimEventSerializer(event).data,
            status=status.HTTP_200_OK,
        )


class ApproveClaimView(
    ClaimWorkflowActionView
):
    def post(self, request, pk):
        claim = self.get_claim(pk)

        if claim is None:
            return Response(
                {
                    "error": {
                        "code": "CLAIM_NOT_FOUND",
                        "message": "Claim not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ClaimApprovalSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        event = (
            ClaimWorkflowService
            .approve_claim(
                claim=claim,
                actor=request.user,
                approved_amount=serializer.validated_data[
                    "approved_amount"
                ],
                comment=serializer.validated_data.get(
                    "comment",
                    "",
                ),
            )
        )

        return Response(
            ClaimEventSerializer(event).data,
            status=status.HTTP_200_OK,
        )


class RejectClaimView(
    ClaimWorkflowActionView
):
    def post(self, request, pk):
        claim = self.get_claim(pk)

        if claim is None:
            return Response(
                {
                    "error": {
                        "code": "CLAIM_NOT_FOUND",
                        "message": "Claim not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ClaimRejectionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        event = (
            ClaimWorkflowService
            .reject_claim(
                claim=claim,
                actor=request.user,
                reason=serializer.validated_data[
                    "reason"
                ],
            )
        )

        return Response(
            ClaimEventSerializer(event).data,
            status=status.HTTP_200_OK,
        )


class StartSettlementView(
    ClaimWorkflowActionView
):
    def post(self, request, pk):
        claim = self.get_claim(pk)

        if claim is None:
            return Response(
                {
                    "error": {
                        "code": "CLAIM_NOT_FOUND",
                        "message": "Claim not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        event = (
            ClaimWorkflowService
            .start_settlement(
                claim=claim,
                actor=request.user,
            )
        )

        return Response(
            ClaimEventSerializer(event).data,
            status=status.HTTP_200_OK,
        )


class SettleClaimView(
    ClaimWorkflowActionView
):
    def post(self, request, pk):
        claim = self.get_claim(pk)

        if claim is None:
            return Response(
                {
                    "error": {
                        "code": "CLAIM_NOT_FOUND",
                        "message": "Claim not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ClaimSettlementSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        event = (
            ClaimWorkflowService
            .settle_claim(
                claim=claim,
                actor=request.user,
                settlement_amount=serializer.validated_data[
                    "settlement_amount"
                ],
                payment_reference=serializer.validated_data[
                    "payment_reference"
                ],
            )
        )

        return Response(
            ClaimEventSerializer(event).data,
            status=status.HTTP_200_OK,
        )


class CloseClaimView(
    ClaimWorkflowActionView
):
    def post(self, request, pk):
        claim = self.get_claim(pk)

        if claim is None:
            return Response(
                {
                    "error": {
                        "code": "CLAIM_NOT_FOUND",
                        "message": "Claim not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ClaimActionCommentSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        event = (
            ClaimWorkflowService
            .close_claim(
                claim=claim,
                actor=request.user,
                comment=serializer.validated_data.get(
                    "comment",
                    "",
                ),
            )
        )

        return Response(
            ClaimEventSerializer(event).data,
            status=status.HTTP_200_OK,
        )


class ClaimEventListView(
    generics.ListAPIView
):
    """
    GET /api/v1/claims/{claim_id}/events/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = ClaimEventSerializer

    def get_queryset(self):
        queryset = (
            ClaimEvent.objects
            .select_related("actor")
            .filter(
                claim_id=self.kwargs["claim_id"]
            )
        )

        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            queryset = queryset.filter(
                claim__policy__customer__user=user
            )

        return queryset


class ClaimRequirementListView(
    generics.ListAPIView
):
    """
    GET /api/v1/claims/{claim_id}/requirements/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = (
        ClaimDocumentRequirementSerializer
    )

    def get_queryset(self):
        queryset = (
            ClaimDocumentRequirement.objects
            .filter(
                claim_id=self.kwargs[
                    "claim_id"
                ]
            )
        )

        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            queryset = queryset.filter(
                claim__policy__customer__user=user
            )

        return queryset


class ClaimSettlementDetailView(
    generics.RetrieveAPIView
):
    """
    GET /api/v1/claims/{claim_id}/settlement/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = (
        ClaimSettlementResponseSerializer
    )

    def get_object(self):
        claim_queryset = Claim.objects.all()

        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            claim_queryset = claim_queryset.filter(
                policy__customer__user=user
            )

        claim = get_object_or_404(
            claim_queryset,
            id=self.kwargs["claim_id"],
        )

        return get_object_or_404(
            ClaimSettlement,
            claim=claim,
        )