from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .snowflake.client import SnowflakeClient


class SnowflakeHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            client = SnowflakeClient()

            (
                account,
                user,
                role,
                warehouse,
                database,
                schema,
            ) = client.test_connection()

            return Response(
                {
                    "status": "CONNECTED",
                    "snowflake": {
                        "account": account,
                        "user": user,
                        "role": role,
                        "warehouse": warehouse,
                        "database": database,
                        "schema": schema,
                    },
                }
            )

        except Exception as exc:
            return Response(
                {
                    "status": "FAILED",
                    "error": str(exc),
                },
                status=500,
            )