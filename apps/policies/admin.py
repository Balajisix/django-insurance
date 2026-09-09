from django.contrib import admin

from .models import Coverage, Policy


class CoverageInline(admin.TabularInline):
    model = Coverage
    extra = 0


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = (
        "policy_number",
        "customer",
        "policy_type",
        "status",
        "start_date",
        "end_date",
        "premium",
    )

    search_fields = (
        "policy_number",
        "customer__customer_number",
        "customer__user__username",
    )

    list_filter = (
        "policy_type",
        "status",
    )

    readonly_fields = (
        "policy_number",
        "created_at",
        "updated_at",
    )

    inlines = [
        CoverageInline,
    ]