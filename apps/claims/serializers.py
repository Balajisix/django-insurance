from rest_framework import serializers

from .models import (
    Claim,
    ClaimDocumentRequirement,
    ClaimEvent,
    ClaimSettlement,
    ClaimType,
)


class ClaimSerializer(
    serializers.ModelSerializer
):
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


class ClaimCreateSerializer(
    serializers.Serializer
):
    policy_id = serializers.IntegerField()

    claim_type = serializers.ChoiceField(
        choices=ClaimType.choices,
    )

    incident_date = serializers.DateField()

    incident_description = (
        serializers.CharField(
            allow_blank=False,
        )
    )

    estimated_loss = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
    )


class ClaimActionCommentSerializer(
    serializers.Serializer
):
    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
    )


class ClaimInformationRequestSerializer(
    serializers.Serializer
):
    comment = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
    )


class ClaimApprovalSerializer(
    serializers.Serializer
):
    approved_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
    )

    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
    )


class ClaimRejectionSerializer(
    serializers.Serializer
):
    reason = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
    )


class ClaimSettlementSerializer(
    serializers.Serializer
):
    settlement_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
    )

    payment_reference = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=100,
    )


class ClaimEventSerializer(
    serializers.ModelSerializer
):
    actor_email = serializers.EmailField(
        source="actor.email",
        read_only=True,
    )

    class Meta:
        model = ClaimEvent

        fields = [
            "id",
            "event_type",
            "from_status",
            "to_status",
            "comment",
            "actor",
            "actor_email",
            "created_at",
        ]

        read_only_fields = fields


class ClaimDocumentRequirementSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = ClaimDocumentRequirement

        fields = [
            "id",
            "document_type",
            "description",
            "is_required",
            "is_fulfilled",
            "fulfilled_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


class ClaimSettlementResponseSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = ClaimSettlement

        fields = [
            "id",
            "claim",
            "settlement_amount",
            "payment_reference",
            "settled_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields