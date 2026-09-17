import pandas as pd

from apps.customers.models import Customer
from apps.policies.models import Policy
from apps.claims.models import Claim, ClaimSettlement, ClaimAIAnalysis


class PostgreSQLExtractor:
    """
    Extract transactional data from PostgreSQL using Django ORM.
    """

    def customers(self) -> pd.DataFrame:
        queryset = Customer.objects.values(
            "customer_number",
            "user__first_name",
            "user__last_name",
            "date_of_birth",
            "phone_number",
            "city",
            "state",
            "postal_code",
            "created_at",
            "updated_at",
        )

        df = pd.DataFrame.from_records(queryset)

        if df.empty:
            return df

        df.rename(
            columns={
                "customer_number": "CUSTOMER_NUMBER",
                "user__first_name": "FIRST_NAME",
                "user__last_name": "LAST_NAME",
                "date_of_birth": "DATE_OF_BIRTH",
                "phone_number": "PHONE",
                "city": "CITY",
                "state": "STATE",
                "postal_code": "POSTAL_CODE",
                "created_at": "CREATED_AT",
                "updated_at": "UPDATED_AT",
            },
            inplace=True,
        )

        return df

    def policies(self) -> pd.DataFrame:
        queryset = Policy.objects.values(
            "policy_number",
            "customer__customer_number",
            "policy_type",
            "status",
            "start_date",
            "end_date",
            "premium",
            "created_at",
            "updated_at",
        )

        df = pd.DataFrame.from_records(queryset)

        if df.empty:
            return df

        df.rename(
            columns={
                "policy_number": "POLICY_NUMBER",
                "customer__customer_number": "CUSTOMER_NUMBER",
                "policy_type": "POLICY_TYPE",
                "status": "POLICY_STATUS",
                "start_date": "START_DATE",
                "end_date": "END_DATE",
                "premium": "PREMIUM",
                "created_at": "CREATED_AT",
                "updated_at": "UPDATED_AT",
            },
            inplace=True,
        )

        return df

    def claims(self) -> pd.DataFrame:
        """
        Extract claims and explicitly obtain CUSTOMER_NUMBER
        through Claim -> Policy -> Customer.
        """

        queryset = Claim.objects.values(
            "claim_number",
            "policy__policy_number",
            "policy__customer__customer_number",
            "claim_type",
            "status",
            "incident_date",
            "estimated_loss",
            "approved_amount",
            "created_at",
            "updated_at",
        )

        df = pd.DataFrame.from_records(queryset)

        if df.empty:
            return df

        df.rename(
            columns={
                "claim_number": "CLAIM_NUMBER",
                "policy__policy_number": "POLICY_NUMBER",
                "policy__customer__customer_number": "CUSTOMER_NUMBER",
                "claim_type": "CLAIM_TYPE_CODE",
                "status": "CLAIM_STATUS",
                "incident_date": "INCIDENT_DATE",
                "estimated_loss": "ESTIMATED_LOSS",
                "approved_amount": "APPROVED_AMOUNT",
                "created_at": "CREATED_AT",
                "updated_at": "UPDATED_AT",
            },
            inplace=True,
        )

        return df

    def settlements(self) -> pd.DataFrame:
        queryset = ClaimSettlement.objects.values(
            "claim__claim_number",
            "settlement_amount",
            "settled_at",
        )

        df = pd.DataFrame.from_records(queryset)

        if df.empty:
            return df

        df.rename(
            columns={
                "claim__claim_number": "CLAIM_NUMBER",
                "settlement_amount": "SETTLEMENT_AMOUNT",
                "settled_at": "SETTLED_AT",
            },
            inplace=True,
        )

        return df

    def ai_analyses(self) -> pd.DataFrame:
        queryset = ClaimAIAnalysis.objects.values(
            "claim__claim_number",
            "status",
            "structured_result",
            "generated_at",
        )

        df = pd.DataFrame.from_records(queryset)

        if df.empty:
            return df

        df.rename(
            columns={
                "claim__claim_number": "CLAIM_NUMBER",
                "status": "AI_STATUS",
                "structured_result": "STRUCTURED_RESULT",
                "generated_at": "AI_GENERATED_AT",
            },
            inplace=True,
        )

        return df