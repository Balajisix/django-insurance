from django.contrib import admin

from .models import (
    Claim,
    ClaimDocumentRequirement,
    ClaimEvent,
    ClaimSettlement,
    ClaimAIAnalysis,
    ClaimAIMissingInformation
)


class ClaimEventInline(
    admin.TabularInline
):
    model = ClaimEvent
    extra = 0
    readonly_fields = (
        "event_type",
        "from_status",
        "to_status",
        "comment",
        "actor",
        "created_at",
    )


class ClaimRequirementInline(
    admin.TabularInline
):
    model = ClaimDocumentRequirement
    extra = 0
    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        "claim_number",
        "policy",
        "claim_type",
        "status",
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

    inlines = [
        ClaimRequirementInline,
        ClaimEventInline,
    ]


@admin.register(ClaimSettlement)
class ClaimSettlementAdmin(admin.ModelAdmin):
    list_display = (
        "claim",
        "settlement_amount",
        "payment_reference",
        "settled_at",
        "created_at",
    )

    search_fields = (
        "claim__claim_number",
        "payment_reference",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(ClaimDocumentRequirement)
class ClaimDocumentRequirementAdmin(
    admin.ModelAdmin
):
    list_display = (
        "claim",
        "document_type",
        "is_required",
        "is_fulfilled",
        "fulfilled_at",
    )

    list_filter = (
        "document_type",
        "is_required",
        "is_fulfilled",
    )


@admin.register(ClaimEvent)
class ClaimEventAdmin(admin.ModelAdmin):
    list_display = (
        "claim",
        "event_type",
        "from_status",
        "to_status",
        "actor",
        "created_at",
    )

    search_fields = (
        "claim__claim_number",
        "actor__email",
    )

    list_filter = (
        "event_type",
        "from_status",
        "to_status",
    )

    readonly_fields = (
        "claim",
        "event_type",
        "from_status",
        "to_status",
        "comment",
        "actor",
        "created_at",
    )

@admin.register(ClaimAIAnalysis)
class ClaimAIAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "claim",
        "status",
        "model_name",
        "generated_at",
        "created_at",
    )

    list_filter = (
        "status",
        "model_name",
        "created_at",
    )

    search_fields = (
        "claim__claim_number",
        "summary",
        "error_message",
    )

    readonly_fields = (
        "generated_at",
        "created_at",
        "updated_at",
    )

@admin.register(ClaimAIMissingInformation)
class ClaimAIMissingInformationAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "claim",
        "source",
        "document_type",
        "is_resolved",
        "created_at",
    )

    list_filter = (
        "source",
        "is_resolved",
        "created_at",
    )

    search_fields = (
        "claim__claim_number",
        "description",
        "document_type",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )