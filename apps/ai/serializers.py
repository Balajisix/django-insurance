from rest_framework import serializers

from .models import DocumentExtraction, DocumentProcessingJob, DocumentChunk
from apps.claims.models import ClaimAIAnalysis, ClaimAIMissingInformation


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
    
class DocumentSearchSerializer(
    serializers.Serializer
):
    query = serializers.CharField(
        max_length=1000
    )

    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20,
    )

    claim_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
    )

class RAGQuerySerializer(
    serializers.Serializer
):
    question = serializers.CharField(
        max_length=2000,
    )

    claim_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
    )

    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=10,
    )

class RAGSourceSerializer(
    serializers.Serializer
):
    chunk_id = serializers.IntegerField()

    document_id = serializers.IntegerField()

    document_name = serializers.CharField()

    document_type = serializers.CharField()

    chunk_index = serializers.IntegerField()

    score = serializers.FloatField()


class RAGResponseSerializer(
    serializers.Serializer
):
    question = serializers.CharField()

    claim_id = serializers.IntegerField(
        allow_null=True,
    )

    answer = serializers.CharField()

    sources = RAGSourceSerializer(
        many=True
    )

class ClaimAIAnalysisSerializer(
    serializers.ModelSerializer
):
    claim_number = serializers.CharField(
        source="claim.claim_number",
        read_only=True,
    )

    class Meta:
        model = ClaimAIAnalysis
        fields = [
            "id",
            "claim_number",
            "status",
            "summary",
            "structured_result",
            "model_name",
            "error_message",
            "generated_at",
            "created_at",
            "updated_at",
        ]

class RequiredDocumentStatusSerializer(
    serializers.Serializer
):
    document_type = serializers.CharField()

    description = serializers.CharField()

    required = serializers.BooleanField()

    fulfilled = serializers.BooleanField()

    fulfilled_at = serializers.DateTimeField(
        allow_null=True,
    )


class AIMissingInformationSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = ClaimAIMissingInformation

        fields = [
            "id",
            "description",
            "source",
            "document_type",
            "is_resolved",
            "resolved_at",
            "created_at",
        ]