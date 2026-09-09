from rest_framework import serializers

from .models import Claim, ClaimType


class ClaimSerializer(serializers.ModelSerializer):
    policy_number = serializers.CharField(
        source="policy.policy_number",
        read_only=True,
    )

    customer_number = serializers.CharField(
        source="policy.customer.customer_number",
        read_only=True,
    )

    class Meta:
        model = Claim

        fields = [
            "id",
            "claim_number",
            "policy",
            "policy_number",
            "customer_number",
            "claim_type",
            "status",
            "incident_date",
            "incident_description",
            "estimated_loss",
            "approved_amount",
            "ai_summary",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "claim_number",
            "status",
            "policy_number",
            "customer_number",
            "approved_amount",
            "ai_summary",
            "created_at",
            "updated_at",
        ]


class ClaimCreateSerializer(serializers.Serializer):
    policy_id = serializers.IntegerField()

    claim_type = serializers.ChoiceField(
        choices=ClaimType.choices,
    )

    incident_date = serializers.DateField()

    incident_description = serializers.CharField(
        allow_blank=False,
    )

    estimated_loss = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
    )