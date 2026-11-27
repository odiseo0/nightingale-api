"""Allow the separate metrics action for platform operators."""

from alembic import op


revision = "20261127_01"
down_revision = "20261126_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE nightingale.platform_operators "
        "DROP CONSTRAINT ck_platform_operators_actions"
    )
    op.execute(
        "ALTER TABLE nightingale.platform_operators ADD CONSTRAINT "
        "ck_platform_operators_actions CHECK (cardinality(actions) > 0 AND "
        "actions <@ ARRAY['review','catalog','rates','operators','metrics']::text[])"
    )


def downgrade():
    op.execute(
        "DELETE FROM nightingale.platform_operators WHERE actions @> ARRAY['metrics']::text[]"
    )
    op.execute(
        "ALTER TABLE nightingale.platform_operators "
        "DROP CONSTRAINT ck_platform_operators_actions"
    )
    op.execute(
        "ALTER TABLE nightingale.platform_operators ADD CONSTRAINT "
        "ck_platform_operators_actions CHECK (cardinality(actions) > 0 AND "
        "actions <@ ARRAY['review','catalog','rates','operators']::text[])"
    )
