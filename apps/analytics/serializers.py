from rest_framework import serializers


class ClaimOverviewSerializer(serializers.Serializer):

    total_claims = serializers.IntegerField(
        source="TOTAL_CLAIMS"
    )

    claim_count = serializers.IntegerField(
        source="CLAIM_COUNT"
    )

    total_estimated_loss = serializers.DecimalField(
        source="TOTAL_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_approved_amount = serializers.DecimalField(
        source="TOTAL_APPROVED_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_settlement_amount = serializers.DecimalField(
        source="TOTAL_SETTLEMENT_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_estimated_loss = serializers.DecimalField(
        source="AVG_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_approved_amount = serializers.DecimalField(
        source="AVG_APPROVED_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_settlement_amount = serializers.DecimalField(
        source="AVG_SETTLEMENT_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_processing_days = serializers.FloatField(
        source="AVG_PROCESSING_DAYS",
        allow_null=True,
    )

    ai_review_required_claims = serializers.IntegerField(
        source="AI_REVIEW_REQUIRED_CLAIMS"
    )

    settled_claims = serializers.IntegerField(
        source="SETTLED_CLAIMS"
    )

    closed_claims = serializers.IntegerField(
        source="CLOSED_CLAIMS"
    )

    settlement_rate = serializers.DecimalField(
        source="SETTLEMENT_RATE",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )


class ClaimTypeAnalyticsSerializer(
    serializers.Serializer
):

    claim_type_code = serializers.CharField(
        source="CLAIM_TYPE_CODE"
    )

    claim_type_name = serializers.CharField(
        source="CLAIM_TYPE_NAME"
    )

    total_claims = serializers.IntegerField(
        source="TOTAL_CLAIMS"
    )

    total_estimated_loss = serializers.DecimalField(
        source="TOTAL_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_approved_amount = serializers.DecimalField(
        source="TOTAL_APPROVED_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_settlement_amount = serializers.DecimalField(
        source="TOTAL_SETTLEMENT_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_estimated_loss = serializers.DecimalField(
        source="AVG_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_processing_days = serializers.FloatField(
        source="AVG_PROCESSING_DAYS",
        allow_null=True,
    )

    ai_review_required_claims = serializers.IntegerField(
        source="AI_REVIEW_REQUIRED_CLAIMS"
    )


class ClaimStatusAnalyticsSerializer(
    serializers.Serializer
):

    claim_status = serializers.CharField(
        source="CLAIM_STATUS"
    )

    total_claims = serializers.IntegerField(
        source="TOTAL_CLAIMS"
    )

    total_estimated_loss = serializers.DecimalField(
        source="TOTAL_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_approved_amount = serializers.DecimalField(
        source="TOTAL_APPROVED_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_settlement_amount = serializers.DecimalField(
        source="TOTAL_SETTLEMENT_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_processing_days = serializers.FloatField(
        source="AVG_PROCESSING_DAYS",
        allow_null=True,
    )


class MonthlyClaimTrendSerializer(
    serializers.Serializer
):

    incident_year = serializers.IntegerField(
        source="INCIDENT_YEAR"
    )

    incident_month = serializers.IntegerField(
        source="INCIDENT_MONTH"
    )

    month_start = serializers.DateField(
        source="MONTH_START"
    )

    total_claims = serializers.IntegerField(
        source="TOTAL_CLAIMS"
    )

    total_estimated_loss = serializers.DecimalField(
        source="TOTAL_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_approved_amount = serializers.DecimalField(
        source="TOTAL_APPROVED_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_settlement_amount = serializers.DecimalField(
        source="TOTAL_SETTLEMENT_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_processing_days = serializers.FloatField(
        source="AVG_PROCESSING_DAYS",
        allow_null=True,
    )


class PolicyTypeAnalyticsSerializer(
    serializers.Serializer
):

    policy_type = serializers.CharField(
        source="POLICY_TYPE"
    )

    total_claims = serializers.IntegerField(
        source="TOTAL_CLAIMS"
    )

    total_estimated_loss = serializers.DecimalField(
        source="TOTAL_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_approved_amount = serializers.DecimalField(
        source="TOTAL_APPROVED_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_settlement_amount = serializers.DecimalField(
        source="TOTAL_SETTLEMENT_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_estimated_loss = serializers.DecimalField(
        source="AVG_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_processing_days = serializers.FloatField(
        source="AVG_PROCESSING_DAYS",
        allow_null=True,
    )


class ProcessingAnalyticsSerializer(
    serializers.Serializer
):

    claim_type_code = serializers.CharField(
        source="CLAIM_TYPE_CODE"
    )

    claim_type_name = serializers.CharField(
        source="CLAIM_TYPE_NAME"
    )

    total_claims = serializers.IntegerField(
        source="TOTAL_CLAIMS"
    )

    avg_processing_days = serializers.FloatField(
        source="AVG_PROCESSING_DAYS",
        allow_null=True,
    )

    min_processing_days = serializers.IntegerField(
        source="MIN_PROCESSING_DAYS",
        allow_null=True,
    )

    max_processing_days = serializers.IntegerField(
        source="MAX_PROCESSING_DAYS",
        allow_null=True,
    )

    claims_processed_within_3_days = serializers.IntegerField(
        source="CLAIMS_PROCESSED_WITHIN_3_DAYS"
    )

    claims_processed_within_7_days = serializers.IntegerField(
        source="CLAIMS_PROCESSED_WITHIN_7_DAYS"
    )


class SettlementAnalyticsSerializer(
    serializers.Serializer
):

    claim_type_code = serializers.CharField(
        source="CLAIM_TYPE_CODE"
    )

    claim_type_name = serializers.CharField(
        source="CLAIM_TYPE_NAME"
    )

    total_claims = serializers.IntegerField(
        source="TOTAL_CLAIMS"
    )

    settled_financial_records = serializers.IntegerField(
        source="SETTLED_FINANCIAL_RECORDS"
    )

    total_estimated_loss = serializers.DecimalField(
        source="TOTAL_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_approved_amount = serializers.DecimalField(
        source="TOTAL_APPROVED_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_settlement_amount = serializers.DecimalField(
        source="TOTAL_SETTLEMENT_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    settlement_to_estimated_ratio = serializers.DecimalField(
        source="SETTLEMENT_TO_ESTIMATED_RATIO",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )


class AIAnalyticsSerializer(
    serializers.Serializer
):

    claim_type_code = serializers.CharField(
        source="CLAIM_TYPE_CODE"
    )

    claim_type_name = serializers.CharField(
        source="CLAIM_TYPE_NAME"
    )

    total_claims = serializers.IntegerField(
        source="TOTAL_CLAIMS"
    )

    human_review_required = serializers.IntegerField(
        source="HUMAN_REVIEW_REQUIRED"
    )

    human_review_not_required = serializers.IntegerField(
        source="HUMAN_REVIEW_NOT_REQUIRED"
    )

    human_review_rate = serializers.DecimalField(
        source="HUMAN_REVIEW_RATE",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )


class CustomerClaimsAnalyticsSerializer(
    serializers.Serializer
):

    customer_number = serializers.CharField(
        source="CUSTOMER_NUMBER"
    )

    first_name = serializers.CharField(
        source="FIRST_NAME"
    )

    last_name = serializers.CharField(
        source="LAST_NAME"
    )

    city = serializers.CharField(
        source="CITY",
        allow_blank=True,
        allow_null=True,
    )

    state = serializers.CharField(
        source="STATE",
        allow_blank=True,
        allow_null=True,
    )

    total_claims = serializers.IntegerField(
        source="TOTAL_CLAIMS"
    )

    total_estimated_loss = serializers.DecimalField(
        source="TOTAL_ESTIMATED_LOSS",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_approved_amount = serializers.DecimalField(
        source="TOTAL_APPROVED_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    total_settlement_amount = serializers.DecimalField(
        source="TOTAL_SETTLEMENT_AMOUNT",
        max_digits=38,
        decimal_places=6,
        allow_null=True,
    )

    avg_processing_days = serializers.FloatField(
        source="AVG_PROCESSING_DAYS",
        allow_null=True,
    )

    ai_review_required_claims = serializers.IntegerField(
        source="AI_REVIEW_REQUIRED_CLAIMS"
    )


class ClaimsDashboardSerializer(
    serializers.Serializer
):

    overview = ClaimOverviewSerializer()

    customer_claims = CustomerClaimsAnalyticsSerializer(
        many=True
    )

    claims_by_type = ClaimTypeAnalyticsSerializer(
        many=True
    )

    claims_by_status = ClaimStatusAnalyticsSerializer(
        many=True
    )

    monthly_trend = MonthlyClaimTrendSerializer(
        many=True
    )

    claims_by_policy_type = PolicyTypeAnalyticsSerializer(
        many=True
    )

    processing = ProcessingAnalyticsSerializer(
        many=True
    )

    settlement = SettlementAnalyticsSerializer(
        many=True
    )

    ai = AIAnalyticsSerializer(
        many=True
    )