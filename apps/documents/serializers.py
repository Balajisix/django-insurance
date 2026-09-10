from rest_framework import serializers

from .models import ClaimDocument, DocumentType


class ClaimDocumentSerializer(
    serializers.ModelSerializer
):
    claim_number = serializers.CharField(
        source="claim.claim_number",
        read_only=True,
    )

    uploaded_by_email = serializers.EmailField(
        source="uploaded_by.email",
        read_only=True,
    )

    class Meta:
        model = ClaimDocument

        fields = [
            "id",
            "claim",
            "claim_number",
            "document_type",
            "original_file_name",
            "content_type",
            "file_size",
            "status",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "claim",
            "claim_number",
            "original_file_name",
            "content_type",
            "file_size",
            "status",
            "uploaded_by",
            "uploaded_by_email",
            "created_at",
            "updated_at",
        ]


class ClaimDocumentUploadSerializer(
    serializers.Serializer
):
    document_type = serializers.ChoiceField(
        choices=DocumentType.choices,
    )

    file = serializers.FileField(
        allow_empty_file=False,
    )