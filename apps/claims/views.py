from rest_framework import generics, status
from rest_framework.response import Response

from .models import Claim
from .serializers import (
    ClaimCreateSerializer,
    ClaimSerializer,
)
from .services import ClaimService


class ClaimListCreateView(generics.ListCreateAPIView):
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

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
    queryset = (
        Claim.objects
        .select_related(
            "policy",
            "policy__customer",
        )
        .all()
    )

    serializer_class = ClaimSerializer