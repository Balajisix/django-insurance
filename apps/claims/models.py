from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.common.identifiers import generate_claim_number


class ClaimStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    DOCUMENT_PROCESSING = "DOCUMENT_PROCESSING", "Document Processing"
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
    NATURAL_DISASTER = "NATURAL_DISASTER", "Natural Disaster"
    FIRE = "FIRE", "Fire"
    OTHER = "OTHER", "Other"


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
                condition=Q(estimated_loss__gte=0),
                name="claim_estimated_loss_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(
                    approved_amount__isnull=True
                ) | Q(approved_amount__gte=0),
                name="claim_approved_amount_gte_zero",
            ),
        ]

    def __str__(self):
        return self.claim_number