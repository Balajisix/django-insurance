from rest_framework import serializers

from .models import Coverage, Policy, PolicyType


class CoverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coverage

        fields = [
            "id",
            "coverage_code",
            "name",
            "description",
            "coverage_limit",
            "deductible",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class PolicySerializer(serializers.ModelSerializer):
    customer_number = serializers.CharField(
        source="customer.customer_number",
        read_only=True,
    )

    coverages = CoverageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Policy

        fields = [
            "id",
            "policy_number",
            "customer",
            "customer_number",
            "policy_type",
            "status",
            "start_date",
            "end_date",
            "premium",
            "coverages",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "policy_number",
            "status",
            "customer_number",
            "coverages",
            "created_at",
            "updated_at",
        ]


class PolicyCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()

    policy_type = serializers.ChoiceField(
        choices=PolicyType.choices,
    )

    start_date = serializers.DateField()

    end_date = serializers.DateField()

    premium = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
    )