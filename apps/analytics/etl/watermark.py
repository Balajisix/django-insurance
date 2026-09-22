from apps.analytics.snowflake.client import SnowflakeClient

import pandas as pd

class SnowflakeWatermarkStore:

    TABLE_NAME = "ETL_WATERMARK"

    SOURCE_CUSTOMERS = "CUSTOMERS"
    SOURCE_POLICIES = "POLICIES"
    SOURCE_CLAIMS = "CLAIMS"
    SOURCE_SETTLEMENTS = "SETTLEMENTS"
    SOURCE_AI_ANALYSES = "AI_ANALYSES"

    ALL_SOURCES = [
        SOURCE_CUSTOMERS,
        SOURCE_POLICIES,
        SOURCE_CLAIMS,
        SOURCE_SETTLEMENTS,
        SOURCE_AI_ANALYSES,
    ]

    def __init__(self):
        self.client = SnowflakeClient()

    def ensure_table(self):
        sql = f"""
            CREATE TABLE IF NOT EXISTS
            {self.client.database}.{self.client.schema}.{self.TABLE_NAME}
            (
                SOURCE_ENTITY VARCHAR(50) PRIMARY KEY,
                LAST_UPDATED_AT TIMESTAMP_TZ,
                UPDATED_AT TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
            )
        """

        self.client.execute(sql)

        # Bootstrap the watermark rows.
        # The first incremental run intentionally processes
        # existing rows through MERGE.
        for source in self.ALL_SOURCES:

            merge_sql = f"""
                MERGE INTO
                {self.client.database}.{self.client.schema}.{self.TABLE_NAME} target
                USING (
                    SELECT
                        %s AS SOURCE_ENTITY,
                        TO_TIMESTAMP_TZ('1970-01-01 00:00:00 +00:00')
                            AS LAST_UPDATED_AT
                ) source
                ON target.SOURCE_ENTITY = source.SOURCE_ENTITY

                WHEN NOT MATCHED THEN
                    INSERT (
                        SOURCE_ENTITY,
                        LAST_UPDATED_AT
                    )
                    VALUES (
                        source.SOURCE_ENTITY,
                        source.LAST_UPDATED_AT
                    )
            """

            conn = self.client.connect()

            try:
                cursor = conn.cursor()

                try:
                    cursor.execute(
                        merge_sql,
                        (source,),
                    )

                    conn.commit()

                finally:
                    cursor.close()

            finally:
                conn.close()

    def get_watermarks(self):
        sql = f"""
            SELECT
                SOURCE_ENTITY,
                LAST_UPDATED_AT
            FROM
                {self.client.database}.{self.client.schema}.{self.TABLE_NAME}
        """

        dataframe = self.client.fetch_dataframe(sql)

        if dataframe.empty:
            return {}

        return {
            row["SOURCE_ENTITY"]: row["LAST_UPDATED_AT"]
            for _, row in dataframe.iterrows()
        }

    def update_watermark(
        self,
        connection,
        source_entity: str,
        timestamp,
    ):
        if timestamp is None:
            return

        if isinstance(timestamp, pd.Timestamp):
            timestamp = timestamp.to_pydatetime()

        sql = f"""
            MERGE INTO
            {self.client.database}.{self.client.schema}.{self.TABLE_NAME} target

            USING (
                SELECT
                    %s AS SOURCE_ENTITY,
                    %s AS LAST_UPDATED_AT
            ) source

            ON target.SOURCE_ENTITY = source.SOURCE_ENTITY

            WHEN MATCHED
                AND source.LAST_UPDATED_AT > target.LAST_UPDATED_AT
            THEN
                UPDATE SET
                    LAST_UPDATED_AT = source.LAST_UPDATED_AT,
                    UPDATED_AT = CURRENT_TIMESTAMP()

            WHEN NOT MATCHED THEN
                INSERT (
                    SOURCE_ENTITY,
                    LAST_UPDATED_AT
                )
                VALUES (
                    source.SOURCE_ENTITY,
                    source.LAST_UPDATED_AT
                )
        """

        cursor = connection.cursor()

        try:
            cursor.execute(
                sql,
                (
                    source_entity,
                    timestamp,
                ),
            )

        finally:
            cursor.close()

    def seed_from_dataframes(
        self,
        connection,
        datasets,
    ):
        source_mapping = {
            self.SOURCE_CUSTOMERS: datasets.get("customers"),
            self.SOURCE_POLICIES: datasets.get("policies"),
            self.SOURCE_CLAIMS: datasets.get("claims"),
            self.SOURCE_SETTLEMENTS: datasets.get("settlements"),
            self.SOURCE_AI_ANALYSES: datasets.get("ai_analyses"),
        }

        for source_entity, dataframe in source_mapping.items():

            if dataframe is None or dataframe.empty:
                continue

            if "UPDATED_AT" not in dataframe.columns:
                continue

            timestamps = (
                dataframe["UPDATED_AT"]
                .dropna()
            )

            if timestamps.empty:
                continue

            max_timestamp = timestamps.max()

            max_timestamp = pd.to_datetime(
                max_timestamp,
                utc=True
            )

            if pd.isna(max_timestamp):
                continue

            self.update_watermark(
                connection,
                source_entity,
                max_timestamp,
            )