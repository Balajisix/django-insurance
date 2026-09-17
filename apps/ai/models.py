from django.conf import settings
from django.db import models

from apps.documents.models import ClaimDocument


class ProcessingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"

class ExtractionMethod(models.TextChoices):
    TEXT = "TEXT", "Direct Text Extraction"
    OCR = "OCR", "Optical Character Recognition"
    VISION = "VISION", "Visual Analysis"
    OTHER = "OTHER", "Other"


class DocumentProcessingJob(models.Model):
    """
    Represents one attempt to process a claim document.
    """

    document = models.ForeignKey(
        ClaimDocument,
        on_delete=models.CASCADE,
        related_name="processing_jobs",
    )

    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )

    attempt_number = models.PositiveIntegerField(
        default=1,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_processing_jobs",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["document", "status"],
                name="ai_job_doc_status_idx",
            ),
            models.Index(
                fields=["status"],
                name="ai_job_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"ProcessingJob("
            f"document_id={self.document_id}, "
            f"attempt={self.attempt_number}, "
            f"status={self.status}"
            f")"
        )


class DocumentExtraction(models.Model):
    """
    Stores the latest successfully extracted textual content
    for a claim document.
    """

    document = models.OneToOneField(
        ClaimDocument,
        on_delete=models.CASCADE,
        related_name="extraction",
    )

    extracted_text = models.TextField()

    extraction_method = models.CharField(
        max_length=20,
        choices=ExtractionMethod.choices,
    )

    extractor_version = models.CharField(
        max_length=50,
        default="v1",
    )

    character_count = models.PositiveIntegerField(
        default=0,
    )

    extracted_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-extracted_at"]

    def __str__(self):
        return f"Extraction(document_id={self.document_id})"


class DocumentChunk(models.Model):
    """
    A searchable chunk generated from a document's
    extracted text.
    """

    document = models.ForeignKey(
        ClaimDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
    )

    chunk_index = models.PositiveIntegerField()

    text = models.TextField()

    character_count = models.PositiveIntegerField(
        default=0,
    )

    start_character = models.PositiveIntegerField(
        default=0,
    )

    end_character = models.PositiveIntegerField(
        default=0,
    )

    embedding_model = models.CharField(
        max_length=150,
        blank=True,
        default="",
    )

    embedded_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    faiss_index_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["chunk_index"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "document",
                    "chunk_index",
                ],
                name="unique_document_chunk_index",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "document",
                    "chunk_index",
                ],
                name="ai_chunk_doc_index_idx",
            ),
        ]

    def __str__(self):
        return (
            f"DocumentChunk("
            f"document_id={self.document_id}, "
            f"chunk_index={self.chunk_index}"
            f")"
        )

class DocumentVisualAnalysis(models.Model):
    document = models.OneToOneField(
        ClaimDocument,
        on_delete=models.CASCADE,
        related_name="visual_analysis",
    )

    analysis = models.JSONField(
        default=dict,
        blank=True,
    )

    summary = models.TextField(
        blank=True,
        default="",
    )

    model_name = models.CharField(
        max_length=150,
        blank=True,
        default="",
    )

    analyzed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"DocumentVisualAnalysis("
            f"document_id={self.document_id}"
            f")"
        )