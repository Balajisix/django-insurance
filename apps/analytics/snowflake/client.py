import snowflake.connector
from django.conf import settings
import pandas as pd


class SnowflakeClient:
    """
    Handles connections and SQL execution against Snowflake.
    """

    account = settings.SNOWFLAKE_ACCOUNT
    user = settings.SNOWFLAKE_USER
    password = settings.SNOWFLAKE_PASSWORD
    warehouse = settings.SNOWFLAKE_WAREHOUSE
    database = settings.SNOWFLAKE_DATABASE
    schema = settings.SNOWFLAKE_SCHEMA
    role = settings.SNOWFLAKE_ROLE

    def connect(self):

        return snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema,
            role=self.role,
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

    def execute_many(
        self,
        query: str,
        data,
    ):

        connection = None
        cursor = None

        try:

            connection = self.connect()

            cursor = connection.cursor()

            cursor.executemany(
                query,
                data,
            )

            connection.commit()

        finally:

            if cursor is not None:
                cursor.close()

            if connection is not None:
                connection.close()

    def fetch_dataframe(self, sql: str):
        conn = self.connect()

        try:
            cursor = conn.cursor()

            try:
                cursor.execute(sql)

                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                return pd.DataFrame(rows, columns=columns)

            finally:
                cursor.close()

        finally:
            conn.close()

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