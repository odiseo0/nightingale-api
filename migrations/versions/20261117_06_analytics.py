"""Analytic projection schema: measurement points and durable ETL cursor."""

from alembic import op

revision = "20261117_06"
down_revision = "20261117_05"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA analytics")
    op.execute("""
        CREATE TABLE analytics.measurement_points (
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            measurement_kind text NOT NULL,
            measured_at timestamptz NOT NULL CHECK (isfinite(measured_at)),
            source_measurement_id uuid NOT NULL,
            source_version integer NOT NULL CHECK (source_version>0),
            value numeric,
            systolic_value numeric,
            diastolic_value numeric,
            unit text NOT NULL,
            change_seq bigint NOT NULL,
            PRIMARY KEY (account_id,patient_id,measurement_kind,measured_at,source_measurement_id),
            CHECK (source_measurement_id IS NOT NULL)
        )
    """)
    op.execute("""
        CREATE TABLE analytics.etl_state (
            account_id uuid PRIMARY KEY,
            last_change_seq bigint NOT NULL,
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at))
        )
    """)
    op.execute("CREATE INDEX ix_analytic_points_source ON analytics.measurement_points(account_id,source_measurement_id)")
    op.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON analytics.measurement_points TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON analytics.etl_state TO nightingale_runtime")


def downgrade():
    op.execute("DROP SCHEMA analytics CASCADE")
