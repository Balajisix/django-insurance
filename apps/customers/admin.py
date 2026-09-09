from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "customer_number",
        "user",
        "city",
        "state",
        "created_at",
    )

    search_fields = (
        "customer_number",
        "user__username",
        "user__email",
        "phone_number",
    )

    list_filter = (
        "state",
        "city",
    )

    readonly_fields = (
        "customer_number",
        "created_at",
        "updated_at",
    )