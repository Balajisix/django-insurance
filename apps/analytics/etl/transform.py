import json

import pandas as pd


class SnowflakeTransformer:
    """
    Transform PostgreSQL data into Snowflake warehouse format.
    """

    # DIM CUSTOMER
    def dim_customer(self, customers: pd.DataFrame) -> pd.DataFrame:
        """
        Transform PostgreSQL Customer data into DIM_CUSTOMER format.
        """

        if customers.empty:
            return pd.DataFrame()

        df = customers.copy()

        # Normalize column names
        df.columns = [
            str(column).upper()
            for column in df.columns
        ]

        required_columns = [
            "CUSTOMER_NUMBER",
            "FIRST_NAME",
            "LAST_NAME",
            "DATE_OF_BIRTH",
            "PHONE",
            "CITY",
            "STATE",
            "POSTAL_CODE",
            "CREATED_AT",
            "UPDATED_AT",
        ]

        missing = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"DIM_CUSTOMER missing columns: {missing}"
            )

        return df[required_columns].copy()

    # DIM POLICY
    def dim_policy(self, policies: pd.DataFrame) -> pd.DataFrame:
        """
        Transform PostgreSQL Policy data into DIM_POLICY format.
        """

        if policies.empty:
            return pd.DataFrame()

        df = policies.copy()

        df.columns = [
            str(column).upper()
            for column in df.columns
        ]

        required_columns = [
            "POLICY_NUMBER",
            "CUSTOMER_NUMBER",
            "POLICY_TYPE",
            "POLICY_STATUS",
            "START_DATE",
            "END_DATE",
            "PREMIUM",
            "CREATED_AT",
            "UPDATED_AT",
        ]

        missing = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"DIM_POLICY missing columns: {missing}"
            )

        return df[required_columns].copy()

    # DATE KEY
    @staticmethod
    def date_key(value):
        """
        Convert a date/datetime into YYYYMMDD integer.

        Example:
            2026-09-17 -> 20260917
        """

        if pd.isna(value):
            return None

        parsed = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(parsed):
            return None

        return int(parsed.strftime("%Y%m%d"))

    # AI HUMAN REVIEW FLAG
    @staticmethod
    def get_human_review_required(value) -> bool:
        """
        Extract human_review_required from AI structured JSON.
        """

        if value is None:
            return False

        # Sometimes JSON may arrive as a string.
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return False

        if not isinstance(value, dict):
            return False

        return bool(
            value.get(
                "human_review_required",
                False,
            )
        )

    # FACT CLAIM
    def fact_claim(
        self,
        claims: pd.DataFrame,
        settlements: pd.DataFrame,
        ai_analyses: pd.DataFrame,
    ) -> pd.DataFrame:
        if claims.empty:
            return pd.DataFrame()

        df = claims.copy()

        # Normalize claim column names

        df.columns = [
            str(column).upper()
            for column in df.columns
        ]

        required_claim_columns = [
            "CLAIM_NUMBER",
            "POLICY_NUMBER",
            "CUSTOMER_NUMBER",
            "CLAIM_TYPE_CODE",
            "CLAIM_STATUS",
            "INCIDENT_DATE",
            "ESTIMATED_LOSS",
            "APPROVED_AMOUNT",
            "CREATED_AT",
            "UPDATED_AT",
        ]

        missing = [
            column
            for column in required_claim_columns
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"FACT_CLAIM source missing columns: {missing}"
            )

        # Settlement data
        if settlements is not None and not settlements.empty:

            settlement_df = settlements.copy()

            settlement_df.columns = [
                str(column).upper()
                for column in settlement_df.columns
            ]

            required_settlement_columns = [
                "CLAIM_NUMBER",
                "SETTLEMENT_AMOUNT",
                "SETTLED_AT",
            ]

            settlement_missing = [
                column
                for column in required_settlement_columns
                if column not in settlement_df.columns
            ]

            if settlement_missing:
                raise ValueError(
                    "Settlement data missing columns: "
                    f"{settlement_missing}"
                )

            # One settlement per claim in current model.
            # Keep latest record defensively.
            settlement_df = (
                settlement_df[
                    required_settlement_columns
                ]
                .drop_duplicates(
                    subset=["CLAIM_NUMBER"],
                    keep="last",
                )
            )

            df = df.merge(
                settlement_df,
                on="CLAIM_NUMBER",
                how="left",
            )

        else:

            df["SETTLEMENT_AMOUNT"] = None
            df["SETTLED_AT"] = None

        # AI analysis
        if ai_analyses is not None and not ai_analyses.empty:

            ai_df = ai_analyses.copy()

            ai_df.columns = [
                str(column).upper()
                for column in ai_df.columns
            ]

            required_ai_columns = [
                "CLAIM_NUMBER",
                "STRUCTURED_RESULT",
            ]

            ai_missing = [
                column
                for column in required_ai_columns
                if column not in ai_df.columns
            ]

            if ai_missing:
                raise ValueError(
                    "AI analysis data missing columns: "
                    f"{ai_missing}"
                )

            ai_df["AI_REVIEW_REQUIRED"] = (
                ai_df["STRUCTURED_RESULT"]
                .apply(
                    self.get_human_review_required
                )
            )

            # Keep one AI record per claim.
            ai_df = (
                ai_df[
                    [
                        "CLAIM_NUMBER",
                        "AI_REVIEW_REQUIRED",
                    ]
                ]
                .drop_duplicates(
                    subset=["CLAIM_NUMBER"],
                    keep="last",
                )
            )

            df = df.merge(
                ai_df,
                on="CLAIM_NUMBER",
                how="left",
            )

        else:

            df["AI_REVIEW_REQUIRED"] = False

        # Normalize AI flag
        df["AI_REVIEW_REQUIRED"] = (
            df["AI_REVIEW_REQUIRED"]
            .fillna(False)
            .astype(bool)
        )

        # Date conversions
        incident_dates = pd.to_datetime(
            df["INCIDENT_DATE"],
            errors="coerce",
        )

        created_dates = pd.to_datetime(
            df["CREATED_AT"],
            errors="coerce",
        )

        settled_dates = pd.to_datetime(
            df["SETTLED_AT"],
            errors="coerce",
        )

        df["INCIDENT_DATE_KEY"] = (
            incident_dates
            .apply(self.date_key)
        )

        df["SUBMITTED_DATE_KEY"] = (
            created_dates
            .apply(self.date_key)
        )

        df["SETTLEMENT_DATE_KEY"] = (
            settled_dates
            .apply(self.date_key)
        )

        # Processing days
        df["PROCESSING_DAYS"] = (
            settled_dates - created_dates
        ).dt.days

        # Claim count
        df["CLAIM_COUNT"] = 1

        # Numeric measures
        numeric_columns = [
            "ESTIMATED_LOSS",
            "APPROVED_AMOUNT",
            "SETTLEMENT_AMOUNT",
        ]

        for column in numeric_columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        # Final temporary fact DataFrame
        result_columns = [
            "CLAIM_NUMBER",
            "CUSTOMER_NUMBER",
            "POLICY_NUMBER",
            "CLAIM_TYPE_CODE",
            "INCIDENT_DATE_KEY",
            "SUBMITTED_DATE_KEY",
            "SETTLEMENT_DATE_KEY",
            "CLAIM_STATUS",
            "ESTIMATED_LOSS",
            "APPROVED_AMOUNT",
            "SETTLEMENT_AMOUNT",
            "CLAIM_COUNT",
            "PROCESSING_DAYS",
            "AI_REVIEW_REQUIRED",
            "CREATED_AT",
            "UPDATED_AT",
        ]

        result = df[
            result_columns
        ].copy()

        return result