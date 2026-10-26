"""Separate runtime data from migration metadata and schema ownership."""

from alembic import op


revision = "20261024_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA nightingale")
    op.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
    op.execute("REVOKE ALL ON SCHEMA nightingale FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA nightingale TO nightingale_runtime")


def downgrade():
    # No CASCADE: refuse to remove a schema that still contains data tables.
    op.execute("DROP SCHEMA nightingale")
    op.execute("GRANT USAGE ON SCHEMA public TO PUBLIC")
