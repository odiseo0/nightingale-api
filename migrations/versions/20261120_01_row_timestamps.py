"""Add database defaults for inherited row timestamps."""

from alembic import op


revision = "20261120_01"
down_revision = "20261118_05"
branch_labels = None
depends_on = None

STAMP_TABLES = (
    "account_device_accesses",
    "account_invitations",
    "account_memberships",
    "account_patients",
    "account_professionals",
    "account_sync_heads",
    "accounts",
    "app_users",
    "appointments",
    "care_plan_actions",
    "care_plan_goals",
    "care_plan_reviews",
    "care_plans",
    "clinical_encounters",
    "contact_people",
    "declared_medications",
    "dental_findings",
    "dental_treatments",
    "devices",
    "diagnostic_report_results",
    "diagnostic_reports",
    "patient_allergy_intolerances",
    "patient_antecedents",
    "patient_clinical_profiles",
    "patient_clinical_section_reviews",
    "patient_conditions",
    "patient_contact_relationships",
    "patient_identifiers",
    "patient_immunizations",
    "patient_measurements",
    "patient_notes",
    "patients",
    "professional_services",
    "professionals",
    "report_attachments",
    "schedule_blocks",
    "schedule_exceptions",
    "schedule_rules",
    "services",
    "specialty_records",
    "specialty_templates",
)
CREATED_ONLY_TABLES = ("device_tokens", "sync_snapshots")


def upgrade():
    for table in STAMP_TABLES:
        op.execute(f"""
            ALTER TABLE nightingale.{table}
            ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
            ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP
        """)

    for table in CREATED_ONLY_TABLES:
        op.execute(f"""
            ALTER TABLE nightingale.{table}
            ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP
        """)

    op.execute("""
        ALTER TABLE analytics.etl_state
        ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP
    """)


def downgrade():
    op.execute("ALTER TABLE analytics.etl_state ALTER COLUMN updated_at DROP DEFAULT")

    for table in CREATED_ONLY_TABLES:
        op.execute(f"""
            ALTER TABLE nightingale.{table}
            ALTER COLUMN created_at DROP DEFAULT
        """)

    for table in STAMP_TABLES:
        op.execute(f"""
            ALTER TABLE nightingale.{table}
            ALTER COLUMN created_at DROP DEFAULT,
            ALTER COLUMN updated_at DROP DEFAULT
        """)

