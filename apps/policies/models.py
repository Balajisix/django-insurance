from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.common.identifiers import generate_policy_number


class PolicyStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"
    LAPSED = "LAPSED", "Lapsed"


class PolicyType(models.TextChoices):
    MOTOR = "MOTOR", "Motor Insurance"
    LIFE = "LIFE", "Life Insurance"
    HEALTH = "HEALTH", "Health Insurance"
    PROPERTY = "PROPERTY", "Property Insurance"


class Policy(models.Model):
    """
    Represents an insurance policy owned by a customer.
    """

    policy_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        default=generate_policy_number,
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="policies",
    )

    policy_type = models.CharField(
        max_length=20,
        choices=PolicyType.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=PolicyStatus.choices,
        default=PolicyStatus.ACTIVE,
    )

    start_date = models.DateField()

    end_date = models.DateField()

    premium = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "policies"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=models.F("start_date")),
                name="policy_end_date_gte_start_date",
            ),
            models.CheckConstraint(
                condition=Q(premium__gte=0),
                name="policy_premium_gte_zero",
            ),
        ]

    def __str__(self):
        return self.policy_number


class Coverage(models.Model):
    """
    Represents a coverage attached to an insurance policy.
    """

    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name="coverages",
    )

    coverage_code = models.CharField(
        max_length=30,
    )

    name = models.CharField(
        max_length=100,
    )

    description = models.TextField(
        blank=True,
    )

    coverage_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
        ],
    )

    deductible = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
        ],
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "policy_coverages"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["policy", "coverage_code"],
                name="unique_policy_coverage_code",
            ),
        ]

    def __str__(self):
        return f"{self.policy.policy_number} - {self.name}"