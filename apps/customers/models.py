from django.conf import settings
from django.db import models

from apps.common.identifiers import generate_customer_number


class Customer(models.Model):
    customer_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        default=generate_customer_number,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    address_line = models.CharField(
        max_length=255,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "customers"
        ordering = ["-created_at"]

    def __str__(self):
        return self.customer_number