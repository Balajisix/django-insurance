import json

import pandas as pd

class SnowflakeTransformer:
    """
    Transform PostgreSQL data into Snowflake warehouse format.
    """
    @staticmethod
    def validate_unique(
        dataframe,
        column,
        dataset_name,
    ):
        duplicates = (
            dataframe[
                dataframe[column].duplicated(
                    keep=False
                )
            ]
        )

        if not duplicates.empty:
            raise ValueError(
                f"Duplicate {column} detected in "
                f"{dataset_name}:\n"
                f"{duplicates.to_string(index=False)}"
            )

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

        self.validate_unique(
            df,
            "CUSTOMER_NUMBER",
            "DIM_CUSTOMER",
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

        self.validate_unique(
            df,
            "POLICY_NUMBER",
            "DIM_POLICY",
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
        if claims is None or claims.empty:
            return pd.DataFrame()

        df = claims.copy()

        # Normalize column names

        df.columns = [
            str(column).upper()
            for column in df.columns
        ]

        required_columns = [
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

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                "FACT_CLAIM source is missing columns: "
                f"{missing_columns}"
            )

        # Normalize claim number

        df["CLAIM_NUMBER"] = (
            df["CLAIM_NUMBER"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        # HARD GRAIN CHECK

        duplicate_source_claims = df[
            df["CLAIM_NUMBER"].duplicated(
                keep=False
            )
        ]

        if not duplicate_source_claims.empty:
            raise ValueError(
                "PostgreSQL claim extraction contains duplicate "
                "CLAIM_NUMBER values:\n"
                f"{duplicate_source_claims.to_string(index=False)}"
            )

        source_claim_count = df["CLAIM_NUMBER"].nunique()

        # Settlement

        if (
            settlements is not None
            and not settlements.empty
        ):

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
                    "Settlement data is missing columns: "
                    f"{settlement_missing}"
                )

            settlement_df["CLAIM_NUMBER"] = (
                settlement_df["CLAIM_NUMBER"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

            settlement_df["SETTLEMENT_AMOUNT"] = (
                pd.to_numeric(
                    settlement_df["SETTLEMENT_AMOUNT"],
                    errors="coerce",
                )
            )

            settlement_df["SETTLED_AT"] = pd.to_datetime(
                settlement_df["SETTLED_AT"],
                errors="coerce",
            )

            # IMPORTANT:
            # Reduce settlements to exactly ONE row per claim.
            settlement_df = (
                settlement_df
                .groupby(
                    "CLAIM_NUMBER",
                    as_index=False,
                )
                .agg(
                    SETTLEMENT_AMOUNT=(
                        "SETTLEMENT_AMOUNT",
                        "sum",
                    ),
                    SETTLED_AT=(
                        "SETTLED_AT",
                        "max",
                    ),
                )
            )

            # This merge must remain one-to-one.
            df = df.merge(
                settlement_df,
                on="CLAIM_NUMBER",
                how="left",
                validate="one_to_one",
            )

        else:

            df["SETTLEMENT_AMOUNT"] = None
            df["SETTLED_AT"] = None

        # Check grain after settlement merge

        if len(df) != source_claim_count:
            raise ValueError(
                "Claim grain changed after settlement merge. "
                f"Expected {source_claim_count} rows, "
                f"got {len(df)}."
            )

        # AI analysis

        if (
            ai_analyses is not None
            and not ai_analyses.empty
        ):

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
                    "AI analysis data is missing columns: "
                    f"{ai_missing}"
                )

            ai_df["CLAIM_NUMBER"] = (
                ai_df["CLAIM_NUMBER"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

            # Determine which timestamp should identify the latest
            # AI result.

            if "UPDATED_AT" in ai_df.columns:

                ai_df["AI_ORDER_TIMESTAMP"] = (
                    pd.to_datetime(
                        ai_df["UPDATED_AT"],
                        errors="coerce",
                    )
                )

            elif "AI_GENERATED_AT" in ai_df.columns:

                ai_df["AI_ORDER_TIMESTAMP"] = (
                    pd.to_datetime(
                        ai_df["AI_GENERATED_AT"],
                        errors="coerce",
                    )
                )

            else:

                ai_df["AI_ORDER_TIMESTAMP"] = pd.NaT

            # Convert AI JSON to review flag

            ai_df["AI_REVIEW_REQUIRED"] = (
                ai_df["STRUCTURED_RESULT"]
                .apply(
                    self.get_human_review_required
                )
            )

            # ONE AI RECORD PER CLAIM

            ai_df = (
                ai_df
                .sort_values(
                    "AI_ORDER_TIMESTAMP"
                )
                .drop_duplicates(
                    subset=["CLAIM_NUMBER"],
                    keep="last",
                )
            )

            ai_df = ai_df[
                [
                    "CLAIM_NUMBER",
                    "AI_REVIEW_REQUIRED",
                ]
            ]

            # One-to-one merge

            df = df.merge(
                ai_df,
                on="CLAIM_NUMBER",
                how="left",
                validate="one_to_one",
            )

        else:

            df["AI_REVIEW_REQUIRED"] = False

        # HARD GRAIN CHECK AGAIN

        if len(df) != source_claim_count:
            raise ValueError(
                "Claim grain changed after AI analysis merge. "
                f"Expected {source_claim_count} rows, "
                f"got {len(df)}."
            )

        # AI boolean normalization

        df["AI_REVIEW_REQUIRED"] = (
            df["AI_REVIEW_REQUIRED"]
            .astype("boolean")
            .fillna(False)
            .astype(bool)
        )

        # Date conversion

        incident_dates = pd.to_datetime(
            df["INCIDENT_DATE"],
            errors="coerce",
        )

        submitted_dates = pd.to_datetime(
            df["CREATED_AT"],
            errors="coerce",
        )

        settlement_dates = pd.to_datetime(
            df["SETTLED_AT"],
            errors="coerce",
        )

        df["INCIDENT_DATE_KEY"] = (
            incident_dates
            .apply(self.date_key)
        )

        df["SUBMITTED_DATE_KEY"] = (
            submitted_dates
            .apply(self.date_key)
        )

        df["SETTLEMENT_DATE_KEY"] = (
            settlement_dates
            .apply(self.date_key)
        )

        # Processing days

        df["PROCESSING_DAYS"] = (
            settlement_dates - submitted_dates
        ).dt.days

        # Claim count

        df["CLAIM_COUNT"] = 1

        # Numeric measures

        for column in [
            "ESTIMATED_LOSS",
            "APPROVED_AMOUNT",
            "SETTLEMENT_AMOUNT",
        ]:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        # Final result

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

        # FINAL GRAIN CHECK

        if len(result) != source_claim_count:
            raise ValueError(
                "FACT_CLAIM grain violation. "
                f"Expected {source_claim_count} rows, "
                f"got {len(result)}."
            )

        duplicate_final_claims = result[
            result["CLAIM_NUMBER"].duplicated(
                keep=False
            )
        ]

        if not duplicate_final_claims.empty:
            raise ValueError(
                "FACT_CLAIM contains duplicate CLAIM_NUMBER "
                "after transformation:\n"
                f"{duplicate_final_claims.to_string(index=False)}"
            )

        print()
        print(
            "FACT_CLAIM transformation validated:"
        )
        print(
            f"Source claims : {source_claim_count}"
        )
        print(
            f"Fact rows     : {len(result)}"
        )

        return result