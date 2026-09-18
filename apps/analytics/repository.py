from typing import Any

from apps.analytics.snowflake.client import SnowflakeClient


class AnalyticsRepositoryError(Exception):
    """Raised when Snowflake analytics data cannot be retrieved."""


class SnowflakeAnalyticsRepository:
    """
    Read-only repository for Snowflake analytics views.
    """

    def __init__(self):
        self.client = SnowflakeClient()

    def _qualified_view_name(self, view_name: str) -> str:
        return (
            f"{self.client.database}."
            f"{self.client.schema}."
            f"{view_name}"
        )

    def _execute_query(
        self,
        connection,
        sql: str,
    ) -> list[dict[str, Any]]:

        cursor = connection.cursor()

        try:
            cursor.execute(sql)

            columns = [
                description[0]
                for description in cursor.description
            ]

            rows = cursor.fetchall()

            return [
                dict(zip(columns, row))
                for row in rows
            ]

        finally:
            cursor.close()

    def fetch_all(
        self,
        view_name: str,
        order_by: str | None = None,
    ) -> list[dict[str, Any]]:

        allowed_views = {
            "VW_CLAIMS_BY_TYPE",
            "VW_CLAIMS_BY_STATUS",
            "VW_CLAIMS_MONTHLY_TREND",
            "VW_CLAIMS_BY_POLICY_TYPE",
            "VW_CLAIMS_PROCESSING_ANALYTICS",
            "VW_CLAIMS_SETTLEMENT_ANALYTICS",
            "VW_CLAIMS_AI_ANALYTICS",
            "VW_CUSTOMER_CLAIMS_ANALYTICS",
        }

        if view_name not in allowed_views:
            raise AnalyticsRepositoryError(
                f"Unsupported analytics view: {view_name}"
            )

        sql = f"""
            SELECT *
            FROM {self._qualified_view_name(view_name)}
        """

        if order_by:
            sql += f" ORDER BY {order_by}"

        connection = self.client.connect()

        try:
            return self._execute_query(
                connection,
                sql,
            )

        except Exception as exc:
            raise AnalyticsRepositoryError(
                f"Failed to query {view_name}: {exc}"
            ) from exc

        finally:
            connection.close()

    def fetch_one(
        self,
        view_name: str,
    ) -> dict[str, Any]:

        if view_name != "VW_CLAIMS_OVERVIEW":
            raise AnalyticsRepositoryError(
                f"Unsupported single-row analytics view: {view_name}"
            )

        sql = f"""
            SELECT *
            FROM {self._qualified_view_name(view_name)}
        """

        connection = self.client.connect()

        try:
            rows = self._execute_query(
                connection,
                sql,
            )

            if not rows:
                raise AnalyticsRepositoryError(
                    f"No analytics result returned from {view_name}"
                )

            return rows[0]

        except AnalyticsRepositoryError:
            raise

        except Exception as exc:
            raise AnalyticsRepositoryError(
                f"Failed to query {view_name}: {exc}"
            ) from exc

        finally:
            connection.close()

    def fetch_dashboard(
        self,
    ) -> dict[str, Any]:

        queries = {
            "overview": f"""
                SELECT *
                FROM {self._qualified_view_name(
                    "VW_CLAIMS_OVERVIEW"
                )}
            """,

            "claims_by_type": f"""
                SELECT *
                FROM {self._qualified_view_name(
                    "VW_CLAIMS_BY_TYPE"
                )}
                ORDER BY TOTAL_CLAIMS DESC
            """,

            "claims_by_status": f"""
                SELECT *
                FROM {self._qualified_view_name(
                    "VW_CLAIMS_BY_STATUS"
                )}
                ORDER BY TOTAL_CLAIMS DESC
            """,

            "monthly_trend": f"""
                SELECT *
                FROM {self._qualified_view_name(
                    "VW_CLAIMS_MONTHLY_TREND"
                )}
                ORDER BY MONTH_START ASC
            """,

            "claims_by_policy_type": f"""
                SELECT *
                FROM {self._qualified_view_name(
                    "VW_CLAIMS_BY_POLICY_TYPE"
                )}
                ORDER BY TOTAL_CLAIMS DESC
            """,

            "processing": f"""
                SELECT *
                FROM {self._qualified_view_name(
                    "VW_CLAIMS_PROCESSING_ANALYTICS"
                )}
                ORDER BY AVG_PROCESSING_DAYS DESC
            """,

            "settlement": f"""
                SELECT *
                FROM {self._qualified_view_name(
                    "VW_CLAIMS_SETTLEMENT_ANALYTICS"
                )}
                ORDER BY TOTAL_SETTLEMENT_AMOUNT DESC
            """,

            "ai": f"""
                SELECT *
                FROM {self._qualified_view_name(
                    "VW_CLAIMS_AI_ANALYTICS"
                )}
                ORDER BY HUMAN_REVIEW_REQUIRED DESC
            """,

            "customer_claims": f"""
                SELECT *
                FROM {self._qualified_view_name(
                    "VW_CUSTOMER_CLAIMS_ANALYTICS"
                )}
                ORDER BY TOTAL_CLAIMS DESC
            """,
        }

        connection = self.client.connect()

        try:
            result = {}

            for key, sql in queries.items():

                rows = self._execute_query(
                    connection,
                    sql,
                )

                if key == "overview":

                    if not rows:
                        raise AnalyticsRepositoryError(
                            "Claims overview returned no data."
                        )

                    result[key] = rows[0]

                else:
                    result[key] = rows

            return result

        except AnalyticsRepositoryError:
            raise

        except Exception as exc:
            raise AnalyticsRepositoryError(
                f"Failed to load analytics dashboard: {exc}"
            ) from exc

        finally:
            connection.close()