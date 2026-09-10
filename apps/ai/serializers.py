from rest_framework import serializers

from .models import DocumentExtraction, DocumentProcessingJob


class DocumentProcessingJobSerializer(serializers.ModelSerializer):
    document_id = serializers.IntegerField(
        source="document.id",
        read_only=True,
    )

    document_name = serializers.CharField(
        source="document.original_file_name",
        read_only=True,
    )

    claim_id = serializers.IntegerField(
        source="document.claim.id",
        read_only=True,
    )

    class Meta:
        model = DocumentProcessingJob
        fields = [
            "id",
            "document_id",
            "document_name",
            "claim_id",
            "status",
            "attempt_number",
            "started_at",
            "completed_at",
            "error_message",
            "created_by",
            "created_at",
            "updated_at",
        ]


class DocumentExtractionSerializer(serializers.ModelSerializer):
    document_id = serializers.IntegerField(
        source="document.id",
        read_only=True,
    )

    document_name = serializers.CharField(
        source="document.original_file_name",
        read_only=True,
    )

    class Meta:
        model = DocumentExtraction
        fields = [
            "id",
            "document_id",
            "document_name",
            "extracted_text",
            "extraction_method",
            "extractor_version",
            "character_count",
            "extracted_at",
            "updated_at",
        ]