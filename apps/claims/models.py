from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.common.identifiers import generate_claim_number


class ClaimStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    DOCUMENT_PROCESSING = (
        "DOCUMENT_PROCESSING",
        "Document Processing",
    )
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    ADDITIONAL_INFO_REQUIRED = (
        "ADDITIONAL_INFO_REQUIRED",
        "Additional Information Required",
    )
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    SETTLEMENT_IN_PROGRESS = (
        "SETTLEMENT_IN_PROGRESS",
        "Settlement in Progress",
    )
    SETTLED = "SETTLED", "Settled"
    CLOSED = "CLOSED", "Closed"

class ClaimType(models.TextChoices):
    ACCIDENT = "ACCIDENT", "Accident"
    THEFT = "THEFT", "Theft"
    NATURAL_DISASTER = (
        "NATURAL_DISASTER",
        "Natural Disaster",
    )
    FIRE = "FIRE", "Fire"
    OTHER = "OTHER", "Other"


class ClaimEventType(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Claim Submitted"
    DOCUMENT_PROCESSING_STARTED = (
        "DOCUMENT_PROCESSING_STARTED",
        "Document Processing Started",
    )
    REVIEW_STARTED = (
        "REVIEW_STARTED",
        "Review Started",
    )
    ADDITIONAL_INFORMATION_REQUESTED = (
        "ADDITIONAL_INFORMATION_REQUESTED",
        "Additional Information Requested",
    )
    REVIEW_RESUMED = (
        "REVIEW_RESUMED",
        "Review Resumed",
    )
    APPROVED = "APPROVED", "Claim Approved"
    REJECTED = "REJECTED", "Claim Rejected"
    SETTLEMENT_STARTED = (
        "SETTLEMENT_STARTED",
        "Settlement Started",
    )
    SETTLED = "SETTLED", "Claim Settled"
    CLOSED = "CLOSED", "Claim Closed"

class AIAnalysisStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"

class MissingInformationSource(models.TextChoices):
    BUSINESS_RULE = "BUSINESS_RULE", "Business Rule"
    AI_OBSERVATION = "AI_OBSERVATION", "AI Observation"

class InconsistencySeverity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"


class InconsistencyType(models.TextChoices):
    DATE_DISCREPANCY = (
        "DATE_DISCREPANCY",
        "Date Discrepancy",
    )

    AMOUNT_DISCREPANCY = (
        "AMOUNT_DISCREPANCY",
        "Amount Discrepancy",
    )

    IDENTIFIER_DISCREPANCY = (
        "IDENTIFIER_DISCREPANCY",
        "Identifier Discrepancy",
    )

    DESCRIPTION_DISCREPANCY = (
        "DESCRIPTION_DISCREPANCY",
        "Description Discrepancy",
    )

    CONFLICTING_INFORMATION = (
        "CONFLICTING_INFORMATION",
        "Conflicting Information",
    )

    OTHER = (
        "OTHER",
        "Other",
    )

class Claim(models.Model):
    """
    Represents an insurance claim raised against a policy.
    """

    claim_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        default=generate_claim_number,
    )

    policy = models.ForeignKey(
        "policies.Policy",
        on_delete=models.PROTECT,
        related_name="claims",
    )

    claim_type = models.CharField(
        max_length=30,
        choices=ClaimType.choices,
    )

    status = models.CharField(
        max_length=40,
        choices=ClaimStatus.choices,
        default=ClaimStatus.SUBMITTED,
    )

    incident_date = models.DateField()

    incident_description = models.TextField()

    estimated_loss = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    approved_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
        ],
    )

    ai_summary = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "claims"
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=Q(
                    estimated_loss__gte=0
                ),
                name="claim_estimated_loss_gte_zero",
            ),
            models.CheckConstraint(
                condition=(
                    Q(approved_amount__isnull=True)
                    | Q(approved_amount__gte=0)
                ),
                name="claim_approved_amount_gte_zero",
            ),
        ]

    def __str__(self):
        return self.claim_number


class ClaimEvent(models.Model):
    """
    Immutable-style audit history for claim workflow events.
    """

    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name="events",
    )

    event_type = models.CharField(
        max_length=50,
        choices=ClaimEventType.choices,
    )

    from_status = models.CharField(
        max_length=40,
        choices=ClaimStatus.choices,
        null=True,
        blank=True,
    )

    to_status = models.CharField(
        max_length=40,
        choices=ClaimStatus.choices,
    )

    comment = models.TextField(
        blank=True,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="claim_events",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "claim_events"
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.claim.claim_number} - "
            f"{self.event_type}"
        )


class ClaimDocumentRequirement(models.Model):
    """
    Represents a document expected for a claim.
    """

    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name="document_requirements",
    )

    document_type = models.CharField(
        max_length=30,
    )

    description = models.CharField(
        max_length=255,
    )

    is_required = models.BooleanField(
        default=True,
    )

    is_fulfilled = models.BooleanField(
        default=False,
    )

    fulfilled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "claim_document_requirements"
        ordering = ["document_type"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "claim",
                    "document_type",
                ],
                name="unique_claim_document_requirement",
            ),
        ]

    def __str__(self):
        return (
            f"{self.claim.claim_number} - "
            f"{self.document_type}"
        )


class ClaimSettlement(models.Model):
    """
    Represents settlement information for a claim.
    """

    claim = models.OneToOneField(
        Claim,
        on_delete=models.PROTECT,
        related_name="settlement",
    )

    settlement_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    payment_reference = models.CharField(
        max_length=100,
        unique=True,
    )

    settled_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "claim_settlements"

    def __str__(self):
        return (
            f"{self.claim.claim_number} - "
            f"{self.payment_reference}"
        )

class ClaimAIAnalysis(models.Model):
    """
    Stores the latest AI-generated analysis for a claim.

    This is an AI assistance record and does not represent
    the final insurance decision.
    """

    claim = models.OneToOneField(
        Claim,
        on_delete=models.CASCADE,
        related_name="ai_analysis",
    )

    status = models.CharField(
        max_length=20,
        choices=AIAnalysisStatus.choices,
        default=AIAnalysisStatus.PENDING,
    )

    summary = models.TextField(
        blank=True,
        default="",
    )

    structured_result = models.JSONField(
        default=dict,
        blank=True,
    )

    model_name = models.CharField(
        max_length=150,
        blank=True,
        default="",
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    generated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"ClaimAIAnalysis("
            f"claim_id={self.claim_id}, "
            f"status={self.status}"
            f")"
        )

class ClaimAIMissingInformation(models.Model):
    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name="ai_missing_information",
    )

    description = models.TextField()

    source = models.CharField(
        max_length=30,
        choices=MissingInformationSource.choices,
    )

    document_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    is_resolved = models.BooleanField(
        default=False,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
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
                fields=[
                    "claim",
                    "source",
                ],
                name="claim_ai_missing_source_idx",
            ),
        ]

    def __str__(self):
        return (
            f"ClaimAIMissingInformation("
            f"claim_id={self.claim_id}, "
            f"source={self.source}"
            f")"
        )

class ClaimAIInconsistency(models.Model):
    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name="ai_inconsistencies",
    )

    inconsistency_type = models.CharField(
        max_length=40,
        choices=InconsistencyType.choices,
    )

    severity = models.CharField(
        max_length=20,
        choices=InconsistencySeverity.choices,
    )

    description = models.TextField()

    source_documents = models.JSONField(
        default=list,
        blank=True,
    )

    requires_human_review = models.BooleanField(
        default=True,
    )

    is_resolved = models.BooleanField(
        default=False,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
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
                fields=[
                    "claim",
                    "is_resolved",
                ],
                name="claim_ai_inconsistency_idx",
            ),
        ]

    def __str__(self):
        return (
            f"ClaimAIInconsistency("
            f"claim_id={self.claim_id}, "
            f"type={self.inconsistency_type}, "
            f"severity={self.severity}"
            f")"
        )