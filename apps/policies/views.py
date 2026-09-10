from django.db.models import Prefetch
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.models import UserRole

from .models import Coverage, Policy
from .serializers import (
    CoverageSerializer,
    PolicyCreateSerializer,
    PolicySerializer,
)
from .services import PolicyService


class PolicyListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/policies/
    POST /api/v1/policies/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    queryset = (
        Policy.objects
        .select_related("customer")
        .prefetch_related(
            Prefetch(
                "coverages",
                queryset=Coverage.objects.filter(
                    is_active=True,
                ),
            )
        )
    )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PolicyCreateSerializer

        return PolicySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            queryset = queryset.filter(
                customer__user=user,
            )

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        policy = PolicyService.create_policy(
            customer_id=data["customer_id"],
            policy_type=data["policy_type"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            premium=data["premium"],
        )

        response_serializer = PolicySerializer(
            policy,
            context=self.get_serializer_context(),
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class PolicyDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/policies/{id}/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    queryset = (
        Policy.objects
        .select_related("customer")
        .prefetch_related("coverages")
    )

    serializer_class = PolicySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            queryset = queryset.filter(
                customer__user=user,
            )

        return queryset


class PolicyCoverageCreateView(generics.CreateAPIView):
    """
    POST /api/v1/policies/{id}/coverages/
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = CoverageSerializer

    def create(self, request, *args, **kwargs):
        policy_id = kwargs["pk"]

        policy_queryset = Policy.objects.all()

        if request.user.role == UserRole.CUSTOMER:
            policy_queryset = policy_queryset.filter(
                customer__user=request.user,
            )

        policy_exists = policy_queryset.filter(
            id=policy_id,
        ).exists()

        if not policy_exists:
            return Response(
                {
                    "error": {
                        "code": "POLICY_NOT_FOUND",
                        "message": "Policy not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

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
                "coverage_limit",
            ),
            deductible=serializer.validated_data.get(
                "deductible",
                0,
            ),
        )

        response_serializer = CoverageSerializer(
            coverage,
            context=self.get_serializer_context(),
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )