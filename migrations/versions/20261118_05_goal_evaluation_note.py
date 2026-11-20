"""Preserve optional care plan goal evaluation notes."""

from alembic import op

revision = "20261118_05"
down_revision = "20261118_04"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("care_plan_goals", "care_plan_goal_histories"):
        op.execute(f"""
            ALTER TABLE nightingale.{table}
            ADD COLUMN evaluation_note text
            CHECK (evaluation_note IS NULL OR btrim(evaluation_note)<>'')
        """)


def downgrade():
    for table in ("care_plan_goal_histories", "care_plan_goals"):
        op.execute(f"ALTER TABLE nightingale.{table} DROP COLUMN evaluation_note")
