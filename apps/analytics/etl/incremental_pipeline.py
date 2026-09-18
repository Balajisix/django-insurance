import pandas as pd

from apps.analytics.etl.extract import PostgreSQLExtractor
from apps.analytics.etl.load import SnowflakeLoader
from apps.analytics.etl.transform import SnowflakeTransformer
from apps.analytics.etl.watermark import SnowflakeWatermarkStore


class IncrementalSnowflakeETLPipeline:
    def __init__(self):
        self.extractor = PostgreSQLExtractor()
        self.transformer = SnowflakeTransformer()
        self.loader = SnowflakeLoader()
        self.watermarks = SnowflakeWatermarkStore()

    # HELPERS
    @staticmethod
    def normalize_key(series):
        return (
            series
            .astype("string")
            .str.strip()
            .str.upper()
        )

    @staticmethod
    def dataframe_max_timestamp(
        dataframe,
        column,
    ):
        if dataframe is None or dataframe.empty:
            return None

        if column not in dataframe.columns:
            return None

        values = pd.to_datetime(
            dataframe[column],
            errors="coerce",
        ).dropna()

        if values.empty:
            return None

        return values.max().to_pydatetime()

    # STAGING

    def create_stage_table(
        self,
        connection,
        stage_table,
        target_table,
        columns,
    ):
        column_sql = ", ".join(columns)

        sql = f"""
            CREATE OR REPLACE TEMPORARY TABLE
            {stage_table}
            AS
            SELECT
                {column_sql}
            FROM
                {target_table}
            WHERE 1 = 0
        """

        cursor = connection.cursor()

        try:
            cursor.execute(sql)

        finally:
            cursor.close()

    # CUSTOMER MERGE

    def merge_customers(
        self,
        connection,
        dataframe,
    ):
        if dataframe.empty:
            return

        target = (
            f"{self.loader.client.database}."
            f"{self.loader.client.schema}."
            f"DIM_CUSTOMER"
        )

        stage = "STG_DIM_CUSTOMER"

        columns = [
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

        self.create_stage_table(
            connection,
            stage,
            target,
            columns,
        )

        self.loader.load_dataframe_on_connection(
            connection,
            dataframe[columns],
            stage,
        )

        sql = f"""
            MERGE INTO {target} target
            USING {stage} source

            ON target.CUSTOMER_NUMBER =
               source.CUSTOMER_NUMBER

            WHEN MATCHED THEN
                UPDATE SET
                    FIRST_NAME = source.FIRST_NAME,
                    LAST_NAME = source.LAST_NAME,
                    DATE_OF_BIRTH = source.DATE_OF_BIRTH,
                    PHONE = source.PHONE,
                    CITY = source.CITY,
                    STATE = source.STATE,
                    POSTAL_CODE = source.POSTAL_CODE,
                    UPDATED_AT = source.UPDATED_AT

            WHEN NOT MATCHED THEN
                INSERT (
                    CUSTOMER_NUMBER,
                    FIRST_NAME,
                    LAST_NAME,
                    DATE_OF_BIRTH,
                    PHONE,
                    CITY,
                    STATE,
                    POSTAL_CODE,
                    CREATED_AT,
                    UPDATED_AT
                )

                VALUES (
                    source.CUSTOMER_NUMBER,
                    source.FIRST_NAME,
                    source.LAST_NAME,
                    source.DATE_OF_BIRTH,
                    source.PHONE,
                    source.CITY,
                    source.STATE,
                    source.POSTAL_CODE,
                    source.CREATED_AT,
                    source.UPDATED_AT
                )
        """

        cursor = connection.cursor()

        try:
            cursor.execute(sql)

        finally:
            cursor.close()

    # POLICY MERGE

    def merge_policies(
        self,
        connection,
        dataframe,
    ):
        if dataframe.empty:
            return

        target = (
            f"{self.loader.client.database}."
            f"{self.loader.client.schema}."
            f"DIM_POLICY"
        )

        stage = "STG_DIM_POLICY"

        columns = [
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

        self.create_stage_table(
            connection,
            stage,
            target,
            columns,
        )

        self.loader.load_dataframe_on_connection(
            connection,
            dataframe[columns],
            stage,
        )

        sql = f"""
            MERGE INTO {target} target
            USING {stage} source

            ON target.POLICY_NUMBER =
               source.POLICY_NUMBER

            WHEN MATCHED THEN
                UPDATE SET
                    CUSTOMER_NUMBER = source.CUSTOMER_NUMBER,
                    POLICY_TYPE = source.POLICY_TYPE,
                    POLICY_STATUS = source.POLICY_STATUS,
                    START_DATE = source.START_DATE,
                    END_DATE = source.END_DATE,
                    PREMIUM = source.PREMIUM,
                    UPDATED_AT = source.UPDATED_AT

            WHEN NOT MATCHED THEN
                INSERT (
                    POLICY_NUMBER,
                    CUSTOMER_NUMBER,
                    POLICY_TYPE,
                    POLICY_STATUS,
                    START_DATE,
                    END_DATE,
                    PREMIUM,
                    CREATED_AT,
                    UPDATED_AT
                )

                VALUES (
                    source.POLICY_NUMBER,
                    source.CUSTOMER_NUMBER,
                    source.POLICY_TYPE,
                    source.POLICY_STATUS,
                    source.START_DATE,
                    source.END_DATE,
                    source.PREMIUM,
                    source.CREATED_AT,
                    source.UPDATED_AT
                )
        """

        cursor = connection.cursor()

        try:
            cursor.execute(sql)

        finally:
            cursor.close()

    # GET SURROGATE KEYS

    def get_dimension_maps(
        self,
        connection,
    ):
        customer_sql = f"""
            SELECT
                CUSTOMER_KEY,
                CUSTOMER_NUMBER
            FROM {self.loader.client.database}
                .{self.loader.client.schema}
                .DIM_CUSTOMER
        """

        policy_sql = f"""
            SELECT
                POLICY_KEY,
                POLICY_NUMBER
            FROM {self.loader.client.database}
                .{self.loader.client.schema}
                .DIM_POLICY
        """

        claim_type_sql = f"""
            SELECT
                CLAIM_TYPE_KEY,
                CLAIM_TYPE_CODE
            FROM {self.loader.client.database}
                .{self.loader.client.schema}
                .DIM_CLAIM_TYPE
        """

        customer_keys = self.fetch_dataframe_on_connection(
            connection,
            customer_sql,
        )

        policy_keys = self.fetch_dataframe_on_connection(
            connection,
            policy_sql,
        )

        claim_type_keys = self.fetch_dataframe_on_connection(
            connection,
            claim_type_sql,
        )

        customer_keys.columns = [
            str(column).upper()
            for column in customer_keys.columns
        ]

        policy_keys.columns = [
            str(column).upper()
            for column in policy_keys.columns
        ]

        claim_type_keys.columns = [
            str(column).upper()
            for column in claim_type_keys.columns
        ]

        customer_map = dict(
            zip(
                customer_keys["CUSTOMER_NUMBER"]
                    .astype(str)
                    .str.strip()
                    .str.upper(),
                customer_keys["CUSTOMER_KEY"],
            )
        )

        policy_map = dict(
            zip(
                policy_keys["POLICY_NUMBER"]
                    .astype(str)
                    .str.strip()
                    .str.upper(),
                policy_keys["POLICY_KEY"],
            )
        )

        claim_type_map = dict(
            zip(
                claim_type_keys["CLAIM_TYPE_CODE"]
                    .astype(str)
                    .str.strip()
                    .str.upper(),
                claim_type_keys["CLAIM_TYPE_KEY"],
            )
        )

        return (
            customer_map,
            policy_map,
            claim_type_map,
        )

    # FACT MERGE

    def merge_fact_claims(
        self,
        connection,
        dataframe,
    ):
        if dataframe.empty:
            return

        dataframe = dataframe.copy()

        dataframe["CUSTOMER_NUMBER"] = self.normalize_key(
            dataframe["CUSTOMER_NUMBER"]
        )

        dataframe["POLICY_NUMBER"] = self.normalize_key(
            dataframe["POLICY_NUMBER"]
        )

        dataframe["CLAIM_TYPE_CODE"] = self.normalize_key(
            dataframe["CLAIM_TYPE_CODE"]
        )

        (
            customer_map,
            policy_map,
            claim_type_map,
        ) = self.get_dimension_maps(
            connection
        )

        dataframe["CUSTOMER_KEY"] = (
            dataframe["CUSTOMER_NUMBER"]
            .map(customer_map)
        )

        dataframe["POLICY_KEY"] = (
            dataframe["POLICY_NUMBER"]
            .map(policy_map)
        )

        dataframe["CLAIM_TYPE_KEY"] = (
            dataframe["CLAIM_TYPE_CODE"]
            .map(claim_type_map)
        )

        # Validate surrogate key resolution

        if dataframe["CUSTOMER_KEY"].isna().any():

            missing = dataframe.loc[
                dataframe["CUSTOMER_KEY"].isna(),
                [
                    "CLAIM_NUMBER",
                    "CUSTOMER_NUMBER",
                ],
            ]

            raise ValueError(
                "Unable to resolve CUSTOMER_KEY:\n"
                f"{missing.to_string(index=False)}"
            )

        if dataframe["POLICY_KEY"].isna().any():

            missing = dataframe.loc[
                dataframe["POLICY_KEY"].isna(),
                [
                    "CLAIM_NUMBER",
                    "POLICY_NUMBER",
                ],
            ]

            raise ValueError(
                "Unable to resolve POLICY_KEY:\n"
                f"{missing.to_string(index=False)}"
            )

        if dataframe["CLAIM_TYPE_KEY"].isna().any():

            missing = dataframe.loc[
                dataframe["CLAIM_TYPE_KEY"].isna(),
                [
                    "CLAIM_NUMBER",
                    "CLAIM_TYPE_CODE",
                ],
            ]

            raise ValueError(
                "Unable to resolve CLAIM_TYPE_KEY:\n"
                f"{missing.to_string(index=False)}"
            )

        # Convert surrogate keys

        dataframe["CUSTOMER_KEY"] = (
            dataframe["CUSTOMER_KEY"].astype(int)
        )

        dataframe["POLICY_KEY"] = (
            dataframe["POLICY_KEY"].astype(int)
        )

        dataframe["CLAIM_TYPE_KEY"] = (
            dataframe["CLAIM_TYPE_KEY"].astype(int)
        )

        # Remove temporary business keys

        fact_columns = [
            "CLAIM_NUMBER",
            "CUSTOMER_KEY",
            "POLICY_KEY",
            "CLAIM_TYPE_KEY",
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

        final_fact = dataframe[
            fact_columns
        ].copy()

        target = (
            f"{self.loader.client.database}."
            f"{self.loader.client.schema}."
            f"FACT_CLAIM"
        )

        stage = "STG_FACT_CLAIM"

        self.create_stage_table(
            connection,
            stage,
            target,
            fact_columns,
        )

        self.loader.load_dataframe_on_connection(
            connection,
            final_fact,
            stage,
        )

        if final_fact["CLAIM_NUMBER"].duplicated().any():
            duplicate_claims = final_fact[
                final_fact["CLAIM_NUMBER"].duplicated(
                    keep=False
                )
            ]

            raise ValueError(
                "Duplicate claims detected before FACT_CLAIM MERGE:\n"
                f"{duplicate_claims.to_string(index=False)}"
            )

        sql = f"""
            MERGE INTO {target} target
            USING {stage} source

            ON target.CLAIM_NUMBER =
               source.CLAIM_NUMBER

            WHEN MATCHED THEN
                UPDATE SET
                    CUSTOMER_KEY = source.CUSTOMER_KEY,
                    POLICY_KEY = source.POLICY_KEY,
                    CLAIM_TYPE_KEY = source.CLAIM_TYPE_KEY,
                    INCIDENT_DATE_KEY = source.INCIDENT_DATE_KEY,
                    SUBMITTED_DATE_KEY = source.SUBMITTED_DATE_KEY,
                    SETTLEMENT_DATE_KEY = source.SETTLEMENT_DATE_KEY,
                    CLAIM_STATUS = source.CLAIM_STATUS,
                    ESTIMATED_LOSS = source.ESTIMATED_LOSS,
                    APPROVED_AMOUNT = source.APPROVED_AMOUNT,
                    SETTLEMENT_AMOUNT = source.SETTLEMENT_AMOUNT,
                    CLAIM_COUNT = source.CLAIM_COUNT,
                    PROCESSING_DAYS = source.PROCESSING_DAYS,
                    AI_REVIEW_REQUIRED = source.AI_REVIEW_REQUIRED,
                    UPDATED_AT = source.UPDATED_AT

            WHEN NOT MATCHED THEN
                INSERT (
                    CLAIM_NUMBER,
                    CUSTOMER_KEY,
                    POLICY_KEY,
                    CLAIM_TYPE_KEY,
                    INCIDENT_DATE_KEY,
                    SUBMITTED_DATE_KEY,
                    SETTLEMENT_DATE_KEY,
                    CLAIM_STATUS,
                    ESTIMATED_LOSS,
                    APPROVED_AMOUNT,
                    SETTLEMENT_AMOUNT,
                    CLAIM_COUNT,
                    PROCESSING_DAYS,
                    AI_REVIEW_REQUIRED,
                    CREATED_AT,
                    UPDATED_AT
                )

                VALUES (
                    source.CLAIM_NUMBER,
                    source.CUSTOMER_KEY,
                    source.POLICY_KEY,
                    source.CLAIM_TYPE_KEY,
                    source.INCIDENT_DATE_KEY,
                    source.SUBMITTED_DATE_KEY,
                    source.SETTLEMENT_DATE_KEY,
                    source.CLAIM_STATUS,
                    source.ESTIMATED_LOSS,
                    source.APPROVED_AMOUNT,
                    source.SETTLEMENT_AMOUNT,
                    source.CLAIM_COUNT,
                    source.PROCESSING_DAYS,
                    source.AI_REVIEW_REQUIRED,
                    source.CREATED_AT,
                    source.UPDATED_AT
                )
        """

        cursor = connection.cursor()

        try:
            cursor.execute(sql)

        finally:
            cursor.close()

    # FETCH DATAFRAME USING EXISTING CONNECTION

    def fetch_dataframe_on_connection(
        self,
        connection,
        sql,
    ):
        cursor = connection.cursor()

        try:
            cursor.execute(sql)

            columns = [
                description[0]
                for description in cursor.description
            ]

            rows = cursor.fetchall()

            return pd.DataFrame(
                rows,
                columns=columns,
            )

        finally:
            cursor.close()

    # UPDATE WATERMARK

    def update_watermarks(
        self,
        connection,
        datasets,
    ):
        source_mapping = {
            self.watermarks.SOURCE_CUSTOMERS:
                datasets["customers"],
            self.watermarks.SOURCE_POLICIES:
                datasets["policies"],
            self.watermarks.SOURCE_CLAIMS:
                datasets["claims"],
            self.watermarks.SOURCE_SETTLEMENTS:
                datasets["settlements"],
            self.watermarks.SOURCE_AI_ANALYSES:
                datasets["ai_analyses"],
        }

        for source, dataframe in source_mapping.items():

            timestamp = self.dataframe_max_timestamp(
                dataframe,
                "UPDATED_AT",
            )

            if timestamp is None:
                continue

            self.watermarks.update_watermark(
                connection,
                source,
                timestamp,
            )

    # RUN

    def run(self):

        print()
        print("Starting PostgreSQL → Snowflake INCREMENTAL ETL...")
        print("=" * 80)

        # 1. Ensure watermark metadata exists

        self.watermarks.ensure_table()

        watermark_values = (
            self.watermarks.get_watermarks()
        )

        customer_watermark = watermark_values.get(
            self.watermarks.SOURCE_CUSTOMERS
        )

        policy_watermark = watermark_values.get(
            self.watermarks.SOURCE_POLICIES
        )

        claim_watermark = watermark_values.get(
            self.watermarks.SOURCE_CLAIMS
        )

        settlement_watermark = watermark_values.get(
            self.watermarks.SOURCE_SETTLEMENTS
        )

        ai_watermark = watermark_values.get(
            self.watermarks.SOURCE_AI_ANALYSES
        )

        print()
        print("Current watermarks:")

        print(
            f"Customers   : {customer_watermark}"
        )

        print(
            f"Policies    : {policy_watermark}"
        )

        print(
            f"Claims      : {claim_watermark}"
        )

        print(
            f"Settlements : {settlement_watermark}"
        )

        print(
            f"AI Analyses : {ai_watermark}"
        )

        # 2. Incremental extraction

        customers = self.extractor.customers(
            since=customer_watermark
        )

        policies = self.extractor.policies(
            since=policy_watermark
        )

        settlements = self.extractor.settlements(
            since=settlement_watermark
        )

        ai_analyses = self.extractor.ai_analyses(
            since=ai_watermark
        )

        # Claims changed directly
        claims = self.extractor.claims(
            since=claim_watermark
        )

        # Claims affected by changed settlements / AI
        affected_claim_numbers = set()

        if not settlements.empty:
            affected_claim_numbers.update(
                settlements["CLAIM_NUMBER"]
                .dropna()
                .tolist()
            )

        if not ai_analyses.empty:
            affected_claim_numbers.update(
                ai_analyses["CLAIM_NUMBER"]
                .dropna()
                .tolist()
            )

        if affected_claim_numbers:

            related_claims = self.extractor.claims(
                since=None,
                claim_numbers=affected_claim_numbers,
            )

            if not related_claims.empty:

                claims = pd.concat(
                    [
                        claims,
                        related_claims,
                    ],
                    ignore_index=True,
                )

                claims = (
                    claims
                    .drop_duplicates(
                        subset=["CLAIM_NUMBER"],
                        keep="last",
                    )
                )

        print()
        print("Incrementally extracted rows:")
        print(
            f"Customers   : {len(customers)}"
        )
        print(
            f"Policies    : {len(policies)}"
        )
        print(
            f"Claims      : {len(claims)}"
        )
        print(
            f"Settlements : {len(settlements)}"
        )
        print(
            f"AI Analyses : {len(ai_analyses)}"
        )

        # 3. Transform

        dim_customer = self.transformer.dim_customer(
            customers
        )

        dim_policy = self.transformer.dim_policy(
            policies
        )

        fact_claim = pd.DataFrame()

        if not claims.empty:

            fact_claim = self.transformer.fact_claim(
                claims=claims,
                settlements=settlements,
                ai_analyses=ai_analyses,
            )

        # 4. Open ONE Snowflake connection

        connection = self.loader.client.connect()

        try:

            # 5. MERGE dimensions

            self.merge_customers(
                connection,
                dim_customer,
            )

            self.merge_policies(
                connection,
                dim_policy,
            )

            # 6. MERGE fact

            self.merge_fact_claims(
                connection,
                fact_claim,
            )

            # 7. Update watermarks ONLY after successful MERGE

            self.update_watermarks(
                connection,
                {
                    "customers": customers,
                    "policies": policies,
                    "claims": claims,
                    "settlements": settlements,
                    "ai_analyses": ai_analyses,
                },
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

        print()
        print("=" * 80)
        print("Incremental ETL completed successfully.")
        print("=" * 80)

        return {
            "customers": len(customers),
            "policies": len(policies),
            "claims": len(claims),
            "settlements": len(settlements),
            "ai_analyses": len(ai_analyses),
        }