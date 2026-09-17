from django.core.management.base import BaseCommand, CommandError

from apps.analytics.etl.pipeline import SnowflakeETLPipeline


class Command(BaseCommand):

    help = "Load PostgreSQL data into Snowflake"

    def handle(self, *args, **options):

        try:
            pipeline = SnowflakeETLPipeline()

            result = pipeline.run()

            self.stdout.write(
                self.style.SUCCESS(
                    "Snowflake ETL completed successfully."
                )
            )

            self.stdout.write(
                f"Customers: {result['customers']}"
            )

            self.stdout.write(
                f"Policies: {result['policies']}"
            )

            self.stdout.write(
                f"Claims: {result['claims']}"
            )

        except Exception as exc:
            raise CommandError(
                f"Snowflake ETL failed: {exc}"
            )