from django.db import migrations


SQL_ADD_COLUMN = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'bhtom_calibration_calibration_data'
    ) THEN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'bhtom_calibration_calibration_data'
              AND column_name = 'cpcs_results'
        ) THEN
            ALTER TABLE bhtom_calibration_calibration_data
            ADD COLUMN cpcs_results jsonb NULL;
        END IF;
    END IF;
END $$;
"""

SQL_DROP_COLUMN = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'bhtom_calibration_calibration_data'
          AND column_name = 'cpcs_results'
    ) THEN
        ALTER TABLE bhtom_calibration_calibration_data
        DROP COLUMN cpcs_results;
    END IF;
END $$;
"""


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=SQL_ADD_COLUMN,
            reverse_sql=SQL_DROP_COLUMN,
        ),
    ]
