from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class DocumentType(models.TextChoices):
    POLICY_DOCUMENT = (
        "POLICY_DOCUMENT",
        "Policy Document",
    )
    ACCIDENT_PHOTO = (
        "ACCIDENT_PHOTO",
        "Accident Photo",
    )
    FIR = "FIR", "FIR"
    REPAIR_ESTIMATE = (
        "REPAIR_ESTIMATE",
        "Repair Estimate",
    )
    MEDICAL_REPORT = (
        "MEDICAL_REPORT",
        "Medical Report",
    )
    OTHER = "OTHER", "Other"


class DocumentStatus(models.TextChoices):
    UPLOADED = "UPLOADED", "Uploaded"
    PROCESSING = "PROCESSING", "Processing"
    PROCESSED = "PROCESSED", "Processed"
    FAILED = "FAILED", "Failed"


class ClaimDocument(models.Model):
    """
    Metadata for a document associated with an insurance claim.

    The actual file is stored in AWS S3.
    """

    claim = models.ForeignKey(
        "claims.Claim",
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
    )

    original_file_name = models.CharField(
        max_length=255,
    )

    s3_key = models.CharField(
        max_length=500,
        unique=True,
    )

    content_type = models.CharField(
        max_length=100,
    )

    file_size = models.PositiveBigIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.UPLOADED,
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_documents",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "claim_documents"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.claim.claim_number} - "
            f"{self.original_file_name}"
        )