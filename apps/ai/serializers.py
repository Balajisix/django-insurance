from rest_framework import serializers

from .models import DocumentExtraction, DocumentProcessingJob, DocumentChunk


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

class DocumentChunkSerializer(
    serializers.ModelSerializer
):
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
        model = DocumentChunk

        fields = [
            "id",
            "document_id",
            "document_name",
            "claim_id",
            "chunk_index",
            "text",
            "character_count",
            "start_character",
            "end_character",
            "created_at",
            "updated_at",
        ]

class DocumentEmbeddingSerializer(
    serializers.ModelSerializer
):
    document_id = serializers.IntegerField(
        source="document.id",
        read_only=True,
    )

    document_name = serializers.CharField(
        source="document.original_file_name",
        read_only=True,
    )

    has_embedding = serializers.SerializerMethodField()

    class Meta:
        model = DocumentChunk

        fields = [
            "id",
            "document_id",
            "document_name",
            "chunk_index",
            "character_count",
            "embedding_model",
            "embedded_at",
            "faiss_index_id",
            "has_embedding",
        ]

    def get_has_embedding(self, obj):
        return (
            obj.faiss_index_id is not None
            and obj.embedding_model != ""
        )