from rest_framework import generics, status
from rest_framework.parsers import (
    FormParser,
    MultiPartParser,
)
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response

from apps.claims.models import Claim
from apps.users.models import UserRole

from .models import ClaimDocument
from .serializers import (
    ClaimDocumentSerializer,
    ClaimDocumentUploadSerializer,
)
from .services import DocumentService


class ClaimDocumentListCreateView(
    generics.ListCreateAPIView
):
    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get_queryset(self):
        queryset = (
            ClaimDocument.objects
            .select_related(
                "claim",
                "uploaded_by",
            )
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

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ClaimDocumentUploadSerializer

        return ClaimDocumentSerializer

    def create(self, request, *args, **kwargs):
        claim_id = kwargs["claim_id"]

        if request.user.role == UserRole.CUSTOMER:
            claim_exists = (
                Claim.objects.filter(
                    id=claim_id,
                    policy__customer__user=request.user,
                ).exists()
            )

            if not claim_exists:
                return Response(
                    {
                        "error": {
                            "code": (
                                "CLAIM_NOT_FOUND"
                            ),
                            "message": (
                                "Claim not found."
                            ),
                        }
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        document = (
            DocumentService
            .upload_claim_document(
                claim_id=claim_id,
                uploaded_by=request.user,
                document_type=serializer.validated_data[
                    "document_type"
                ],
                uploaded_file=serializer.validated_data[
                    "file"
                ],
            )
        )

        response_serializer = (
            ClaimDocumentSerializer(
                document
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ClaimDocumentDetailView(
    generics.RetrieveDestroyAPIView
):
    permission_classes = [
        IsAuthenticated,
    ]

    queryset = (
        ClaimDocument.objects
        .select_related(
            "claim",
            "uploaded_by",
        )
        .all()
    )

    serializer_class = ClaimDocumentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            queryset = queryset.filter(
                claim__policy__customer__user=user
            )

        return queryset

    def perform_destroy(self, instance):
        DocumentService.delete_document(
            document_id=instance.id
        )