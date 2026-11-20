"""Allow the runtime role to use the existing analytics schema."""

from alembic import op

revision = "20261118_02"
down_revision = "20261118_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("GRANT USAGE ON SCHEMA analytics TO nightingale_runtime")


def downgrade():
    op.execute("REVOKE USAGE ON SCHEMA analytics FROM nightingale_runtime")
