from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.policies.models import Policy
from apps.users.models import UserRole

from .models import Claim
from .serializers import (
    ClaimCreateSerializer,
    ClaimSerializer,
)
from .services import ClaimService


class ClaimListCreateView(generics.ListCreateAPIView):
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
            policy_exists = Policy.objects.filter(
                id=data["policy_id"],
                customer__user=request.user,
            ).exists()

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
            estimated_loss=data["estimated_loss"],
        )

        response_serializer = ClaimSerializer(
            claim
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ClaimDetailView(generics.RetrieveAPIView):
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