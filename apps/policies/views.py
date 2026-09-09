from django.db.models import Prefetch
from rest_framework import generics, status
from rest_framework.response import Response

from apps.common.exceptions import PolicyValidationError

from .models import Coverage, Policy
from .serializers import (
    CoverageSerializer,
    PolicyCreateSerializer,
    PolicySerializer,
)
from .services import PolicyService


class PolicyListCreateView(generics.ListCreateAPIView):
    queryset = (
        Policy.objects
        .select_related("customer")
        .prefetch_related(
            Prefetch(
                "coverages",
                queryset=Coverage.objects.filter(
                    is_active=True
                ),
            )
        )
        .all()
    )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PolicyCreateSerializer

        return PolicySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        policy = PolicyService.create_policy(
            customer_id=data["customer_id"],
            policy_type=data["policy_type"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            premium=data["premium"],
        )

        response_serializer = PolicySerializer(
            policy
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class PolicyDetailView(generics.RetrieveAPIView):
    queryset = (
        Policy.objects
        .select_related("customer")
        .prefetch_related("coverages")
        .all()
    )

    serializer_class = PolicySerializer


class PolicyCoverageCreateView(generics.CreateAPIView):
    serializer_class = CoverageSerializer

    def create(self, request, *args, **kwargs):
        policy_id = kwargs["pk"]

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        coverage = PolicyService.add_coverage(
            policy_id=policy_id,
            coverage_code=serializer.validated_data[
                "coverage_code"
            ],
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get(
                "description",
                "",
            ),
            coverage_limit=serializer.validated_data.get(
                "coverage_limit"
            ),
            deductible=serializer.validated_data.get(
                "deductible",
                0,
            ),
        )

        response_serializer = CoverageSerializer(
            coverage
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )