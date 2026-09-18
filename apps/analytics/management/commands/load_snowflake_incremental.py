from django.core.management.base import BaseCommand, CommandError

from apps.analytics.etl.incremental_pipeline import (
    IncrementalSnowflakeETLPipeline,
)


class Command(BaseCommand):

    help = "Incrementally load PostgreSQL changes into Snowflake"

    def handle(self, *args, **options):

        try:

            pipeline = (
                IncrementalSnowflakeETLPipeline()
            )

            result = pipeline.run()

            self.stdout.write(
                self.style.SUCCESS(
                    "Incremental Snowflake ETL completed."
                )
            )

            self.stdout.write(
                f"Customers changed: "
                f"{result['customers']}"
            )

            self.stdout.write(
                f"Policies changed: "
                f"{result['policies']}"
            )

            self.stdout.write(
                f"Claims changed: "
                f"{result['claims']}"
            )

            self.stdout.write(
                f"Settlements changed: "
                f"{result['settlements']}"
            )

            self.stdout.write(
                f"AI analyses changed: "
                f"{result['ai_analyses']}"
            )

        except Exception as exc:

            raise CommandError(
                f"Incremental Snowflake ETL failed: {exc}"
            )