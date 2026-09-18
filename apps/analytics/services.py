from apps.analytics.repository import (
    SnowflakeAnalyticsRepository,
)


class AnalyticsService:

    def __init__(self):
        self.repository = SnowflakeAnalyticsRepository()

    def get_overview(self):
        return self.repository.fetch_one(
            "VW_CLAIMS_OVERVIEW"
        )

    def get_claims_by_type(self):
        return self.repository.fetch_all(
            "VW_CLAIMS_BY_TYPE",
            order_by="TOTAL_CLAIMS DESC",
        )

    def get_claims_by_status(self):
        return self.repository.fetch_all(
            "VW_CLAIMS_BY_STATUS",
            order_by="TOTAL_CLAIMS DESC",
        )

    def get_monthly_trend(self):
        return self.repository.fetch_all(
            "VW_CLAIMS_MONTHLY_TREND",
            order_by="MONTH_START ASC",
        )

    def get_claims_by_policy_type(self):
        return self.repository.fetch_all(
            "VW_CLAIMS_BY_POLICY_TYPE",
            order_by="TOTAL_CLAIMS DESC",
        )

    def get_processing_analytics(self):
        return self.repository.fetch_all(
            "VW_CLAIMS_PROCESSING_ANALYTICS",
            order_by="AVG_PROCESSING_DAYS DESC",
        )

    def get_settlement_analytics(self):
        return self.repository.fetch_all(
            "VW_CLAIMS_SETTLEMENT_ANALYTICS",
            order_by="TOTAL_SETTLEMENT_AMOUNT DESC",
        )

    def get_ai_analytics(self):
        return self.repository.fetch_all(
            "VW_CLAIMS_AI_ANALYTICS",
            order_by="HUMAN_REVIEW_REQUIRED DESC",
        )

    def get_customer_claims(self):
        return self.repository.fetch_all(
            "VW_CUSTOMER_CLAIMS_ANALYTICS",
            order_by="TOTAL_CLAIMS DESC",
        )

    def get_dashboard(self):
        return self.repository.fetch_dashboard()