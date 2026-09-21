from django.db import migrations

CHANNEL = "snowflake_etl"

# (app_label, model_name) of every table the incremental ETL reads from.
SOURCE_MODELS = [
    ("customers", "Customer"),
    ("policies", "Policy"),
    ("claims", "Claim"),
    ("claims", "ClaimSettlement"),
    ("claims", "ClaimAIAnalysis"),
]

FUNCTION_SQL = f"""
CREATE OR REPLACE FUNCTION notify_snowflake_etl()
RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('{CHANNEL}', TG_TABLE_NAME);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


def trigger_name(table):
    return f"trg_{table}_snowflake_etl"


def create_triggers(apps, schema_editor):
    schema_editor.execute(FUNCTION_SQL)

    for app_label, model_name in SOURCE_MODELS:
        table = apps.get_model(app_label, model_name)._meta.db_table

        # Statement-level: a bulk insert/update fires ONE notification,
        # and NOTIFY is delivered only when the transaction commits.
        schema_editor.execute(
            f'DROP TRIGGER IF EXISTS {trigger_name(table)} ON "{table}";'
        )
        schema_editor.execute(
            f"""
            CREATE TRIGGER {trigger_name(table)}
            AFTER INSERT OR UPDATE ON "{table}"
            FOR EACH STATEMENT
            EXECUTE FUNCTION notify_snowflake_etl();
            """
        )


def drop_triggers(apps, schema_editor):
    for app_label, model_name in SOURCE_MODELS:
        table = apps.get_model(app_label, model_name)._meta.db_table
        schema_editor.execute(
            f'DROP TRIGGER IF EXISTS {trigger_name(table)} ON "{table}";'
        )

    schema_editor.execute("DROP FUNCTION IF EXISTS notify_snowflake_etl();")


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0002_initial"),
        ("policies", "0001_initial"),
        ("claims", "0006_claimaiinconsistency"),
    ]

    operations = [
        migrations.RunPython(create_triggers, drop_triggers),
    ]
