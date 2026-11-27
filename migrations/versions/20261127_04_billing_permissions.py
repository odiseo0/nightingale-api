"""Add member billing permissions and the billing sync audience."""

from alembic import op


revision = "20261127_04"
down_revision = "20261127_03"
branch_labels = None
depends_on = None

AUDIENCES = (
    "'members','owner','clinical_profile','clinical_conditions','clinical_allergies',"
    "'clinical_encounters','clinical_notes','clinical_measurements',"
    "'clinical_immunizations','clinical_antecedents','clinical_declared_medications',"
    "'clinical_care_plans','clinical_diagnostic_reports','clinical_specialty_templates'"
)


def upgrade():
    for column in ("billing_read_access", "billing_charges_access", "billing_review_access"):
        op.execute(f"""
            ALTER TABLE nightingale.account_memberships
            ADD COLUMN {column} text NOT NULL DEFAULT 'none',
            ADD CONSTRAINT ck_account_memberships_{column}
                CHECK ({column} IN ('none','granted'))
        """)

    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute(f"""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN ({AUDIENCES},'billing'))
    """)


def downgrade():
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute(f"""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN ({AUDIENCES}))
    """)

    for column in ("billing_review_access", "billing_charges_access", "billing_read_access"):
        op.execute(f"""
            ALTER TABLE nightingale.account_memberships
            DROP CONSTRAINT ck_account_memberships_{column},
            DROP COLUMN {column}
        """)
