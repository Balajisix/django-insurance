import snowflake.connector
from django.conf import settings


class SnowflakeClient:
    """
    Handles connections and SQL execution against Snowflake.
    """

    def connect(self):
        return snowflake.connector.connect(
            account=settings.SNOWFLAKE_ACCOUNT,
            user=settings.SNOWFLAKE_USER,
            password=settings.SNOWFLAKE_PASSWORD,
            warehouse=settings.SNOWFLAKE_WAREHOUSE,
            database=settings.SNOWFLAKE_DATABASE,
            schema=settings.SNOWFLAKE_SCHEMA,
            role=settings.SNOWFLAKE_ROLE,
        )

    def execute(
        self,
        query: str,
        params=None,
    ):
        connection = None
        cursor = None

        try:
            connection = self.connect()

            cursor = connection.cursor()

            cursor.execute(
                query,
                params,
            )

            return cursor.fetchall()

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None:
                connection.close()

    def test_connection(self):
        rows = self.execute(
            """
            SELECT
                CURRENT_ACCOUNT(),
                CURRENT_USER(),
                CURRENT_ROLE(),
                CURRENT_WAREHOUSE(),
                CURRENT_DATABASE(),
                CURRENT_SCHEMA()
            """
        )

        if not rows:
            raise RuntimeError(
                "Snowflake returned no connection information."
            )

        return rows[0]