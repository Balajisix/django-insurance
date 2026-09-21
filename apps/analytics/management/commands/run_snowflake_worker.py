import logging
import time

import psycopg
from django.core.management.base import BaseCommand
from django.db import close_old_connections, connection

from apps.analytics.etl.incremental_pipeline import (
    IncrementalSnowflakeETLPipeline,
)

logger = logging.getLogger(__name__)

CHANNEL = "snowflake_etl"


class Command(BaseCommand):

    help = (
        "Long-running worker: listens for PostgreSQL change "
        "notifications and runs the incremental Snowflake ETL."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--debounce",
            type=float,
            default=5.0,
            help="Seconds of quiet after a change before syncing.",
        )
        parser.add_argument(
            "--max-wait",
            type=float,
            default=30.0,
            help="Longest a burst of changes can delay a sync.",
        )
        parser.add_argument(
            "--fallback-interval",
            type=float,
            default=300.0,
            help="Sync at least this often even with no notifications.",
        )
        parser.add_argument(
            "--retry-delay",
            type=float,
            default=30.0,
            help="Wait after a failed sync before retrying.",
        )

    def handle(self, *args, **options):
        self.debounce = options["debounce"]
        self.max_wait = options["max_wait"]
        self.fallback_interval = options["fallback_interval"]
        self.retry_delay = options["retry_delay"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Snowflake worker listening on '{CHANNEL}' "
                f". Ctrl+C to stop."
            )
        )

        try:
            while True:
                try:
                    self.listen_forever()
                except psycopg.OperationalError as exc:
                    # Lost the LISTEN connection: reconnect. Any changes
                    # missed meanwhile are caught by the startup sync.
                    logger.warning("Listener connection lost: %s", exc)
                    time.sleep(self.retry_delay)
        except KeyboardInterrupt:
            self.stdout.write("Worker stopped.")

    def listen_forever(self):
        settings = connection.settings_dict

        with psycopg.connect(
            dbname=settings["NAME"],
            user=settings["USER"],
            password=settings["PASSWORD"],
            host=settings["HOST"],
            port=settings["PORT"],
            autocommit=True,
        ) as listener:

            listener.execute(f"LISTEN {CHANNEL}")

            # Catch up on anything that changed while we were down.
            self.sync()

            last_sync = time.monotonic()

            while True:
                remaining = self.fallback_interval - (
                    time.monotonic() - last_sync
                )

                got_change = self.wait_for_notification(
                    listener,
                    timeout=max(remaining, 0),
                )

                if got_change:
                    self.drain_burst(listener)

                # Either changes arrived (and the burst settled) or the
                # fallback interval elapsed. The watermark ETL is
                # idempotent, so an extra run is harmless.
                self.sync()
                last_sync = time.monotonic()

    @staticmethod
    def wait_for_notification(listener, timeout):
        for _ in listener.notifies(timeout=timeout, stop_after=1):
            return True
        return False

    def drain_burst(self, listener):
        """
        Coalesce a burst: keep waiting until no notification arrives for
        `debounce` seconds, or `max_wait` has passed since the first one.
        """
        deadline = time.monotonic() + self.max_wait

        while time.monotonic() < deadline:
            timeout = min(
                self.debounce,
                deadline - time.monotonic(),
            )

            if not self.wait_for_notification(listener, timeout):
                return

    def sync(self):
        try:
            result = IncrementalSnowflakeETLPipeline().run()

            logger.info("Snowflake sync done: %s", result)

        except Exception:
            logger.exception(
                "Snowflake sync failed; retrying in %ss",
                self.retry_delay,
            )
            time.sleep(self.retry_delay)

        finally:
            # Long-lived process: drop stale ORM connections.
            close_old_connections()
