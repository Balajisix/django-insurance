from django.contrib import admin

from .models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        "claim_number",
        "policy",
        "claim_type",
        "status",
        "incident_date",
        "estimated_loss",
        "approved_amount",
        "created_at",
    )

    search_fields = (
        "claim_number",
        "policy__policy_number",
        "policy__customer__customer_number",
    )

    list_filter = (
        "claim_type",
        "status",
    )

    readonly_fields = (
        "claim_number",
        "created_at",
        "updated_at",
    )