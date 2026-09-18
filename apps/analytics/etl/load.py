import pandas as pd
from snowflake.connector.pandas_tools import write_pandas

from apps.analytics.snowflake.client import SnowflakeClient


class SnowflakeLoader:

    FACT_CLAIM_COLUMNS = [
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

    def __init__(self):
        self.client = SnowflakeClient()

    def truncate_warehouse(self):
        tables = [
            "FACT_CLAIM",
            "DIM_POLICY",
            "DIM_CUSTOMER",
        ]

        for table in tables:
            sql = f"""
                TRUNCATE TABLE
                {self.client.database}.{self.client.schema}.{table}
            """

            self.client.execute(sql)

    def load_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
    ):
        if df.empty:
            print(f"Skipping {table_name}: DataFrame is empty.")
            return

        print("=" * 80)
        print(
            f"Loading into: "
            f"{self.client.database}.{self.client.schema}.{table_name}"
        )
        print(f"Rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        print("=" * 80)

        conn = self.client.connect()

        try:
            success, nchunks, nrows, output = write_pandas(
                conn,
                df,
                table_name,
                database=self.client.database,
                schema=self.client.schema,
                quote_identifiers=False,
                auto_create_table=False,
                use_logical_type=True,
            )

            if not success:
                raise RuntimeError(
                    f"Snowflake write_pandas failed for {table_name}. "
                    f"Output: {output}"
                )

            print(
                f"Loaded {nrows} rows into "
                f"{self.client.database}.{self.client.schema}.{table_name}"
            )

        finally:
            conn.close()

    def load_dim_customer(self, df: pd.DataFrame):
        self.load_dataframe(
            df,
            "DIM_CUSTOMER",
        )

    def validate_reference_dimensions(self):
        checks = {
            "DIM_CUSTOMER": "CUSTOMER_NUMBER",
            "DIM_POLICY": "POLICY_NUMBER",
            "DIM_CLAIM_TYPE": "CLAIM_TYPE_CODE",
            "DIM_DATE": "DATE_KEY",
        }

        for table, key_column in checks.items():

            sql = f"""
                SELECT
                    {key_column},
                    COUNT(*) AS RECORD_COUNT
                FROM
                    {self.client.database}.{self.client.schema}.{table}
                GROUP BY
                    {key_column}
                HAVING COUNT(*) > 1
            """

            duplicates = self.client.fetch_dataframe(sql)

            if not duplicates.empty:
                raise ValueError(
                    f"Duplicate dimension keys detected in "
                    f"{table} ({key_column}):\n"
                    f"{duplicates.to_string(index=False)}"
                )

    def load_dim_policy(self, df: pd.DataFrame):
        self.load_dataframe(
            df,
            "DIM_POLICY",
        )

    def load_fact_claim(self, df: pd.DataFrame):
        fact_df = df.copy()

        # These are temporary ETL business keys.
        # They are NOT columns in FACT_CLAIM.
        temporary_columns = [
            "CUSTOMER_NUMBER",
            "POLICY_NUMBER",
            "CLAIM_TYPE_CODE",
        ]

        fact_df.drop(
            columns=[
                column
                for column in temporary_columns
                if column in fact_df.columns
            ],
            inplace=True,
        )

        missing_columns = [
            column
            for column in self.FACT_CLAIM_COLUMNS
            if column not in fact_df.columns
        ]

        if missing_columns:
            raise ValueError(
                "FACT_CLAIM is missing required columns: "
                f"{missing_columns}"
            )

        fact_df = fact_df[
            self.FACT_CLAIM_COLUMNS
        ]

        self.load_dataframe(
            fact_df,
            "FACT_CLAIM",
        )

    def get_customer_keys(self) -> pd.DataFrame:
        sql = f"""
            SELECT
                CUSTOMER_KEY,
                CUSTOMER_NUMBER
            FROM
                {self.client.database}.{self.client.schema}.DIM_CUSTOMER
        """

        return self.client.fetch_dataframe(sql)

    def get_policy_keys(self) -> pd.DataFrame:
        sql = f"""
            SELECT
                POLICY_KEY,
                POLICY_NUMBER
            FROM
                {self.client.database}.{self.client.schema}.DIM_POLICY
        """

        return self.client.fetch_dataframe(sql)

    def get_claim_type_keys(self) -> pd.DataFrame:
        sql = f"""
            SELECT
                CLAIM_TYPE_KEY,
                CLAIM_TYPE_CODE
            FROM
                {self.client.database}.{self.client.schema}.DIM_CLAIM_TYPE
        """

        return self.client.fetch_dataframe(sql)

    def load_dataframe_on_connection(
        self,
        connection,
        df: pd.DataFrame,
        table_name: str,
    ):
        """
        Load DataFrame into a table using an existing
        Snowflake connection.

        This is required for temporary staging tables because
        temporary tables belong to the current Snowflake session.
        """

        if df.empty:
            return

        success, nchunks, nrows, output = write_pandas(
            connection,
            df,
            table_name,
            database=self.client.database,
            schema=self.client.schema,
            quote_identifiers=False,
            auto_create_table=False,
            use_logical_type=True,
        )

        if not success:
            raise RuntimeError(
                f"Failed loading staging table {table_name}: "
                f"{output}"
            )

        print(
            f"Staged {nrows} rows into {table_name}"
        )