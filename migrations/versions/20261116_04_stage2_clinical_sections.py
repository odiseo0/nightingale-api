"""Clinical routine section scopes."""

from alembic import op

revision = "20261116_04"
down_revision = "20261116_03"
branch_labels = None
depends_on = None


def upgrade():
    for section in ("encounters", "notes", "measurements", "immunizations", "antecedents"):
        op.execute(f"""
            ALTER TABLE nightingale.account_memberships
            ADD COLUMN {section}_access text NOT NULL DEFAULT 'read_write'
            CHECK ({section}_access IN ('none','read','read_write'))
        """)
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_clinical_sections(value jsonb) RETURNS boolean
        LANGUAGE sql IMMUTABLE AS $$
            SELECT jsonb_typeof(value)='array'
                AND value <@ '["profile","conditions","allergies","encounters","notes","measurements","immunizations","antecedents"]'::jsonb
                AND (SELECT count(*)=count(DISTINCT item)
                    FROM jsonb_array_elements_text(value) AS section(item));
        $$
    """)
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute("""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN (
            'members','owner','clinical_profile','clinical_conditions','clinical_allergies',
            'clinical_encounters','clinical_notes','clinical_measurements',
            'clinical_immunizations','clinical_antecedents'
        ))
    """)
    op.execute("ALTER TABLE nightingale.operation_receipts DROP CONSTRAINT operation_receipts_clinical_section_check")
    op.execute("""
        ALTER TABLE nightingale.operation_receipts
        ADD CONSTRAINT operation_receipts_clinical_section_check
        CHECK (clinical_section IN (
            'profile','conditions','allergies','encounters','notes',
            'measurements','immunizations','antecedents'
        ))
    """)


def downgrade():
    op.execute("ALTER TABLE nightingale.operation_receipts DROP CONSTRAINT operation_receipts_clinical_section_check")
    op.execute("""
        ALTER TABLE nightingale.operation_receipts
        ADD CONSTRAINT operation_receipts_clinical_section_check
        CHECK (clinical_section IN ('profile','conditions','allergies'))
    """)
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute("""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN ('members','owner','clinical_profile','clinical_conditions','clinical_allergies'))
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_clinical_sections(value jsonb) RETURNS boolean
        LANGUAGE sql IMMUTABLE AS $$
            SELECT jsonb_typeof(value)='array'
                AND value <@ '["profile","conditions","allergies"]'::jsonb
                AND (SELECT count(*)=count(DISTINCT item)
                    FROM jsonb_array_elements_text(value) AS section(item));
        $$
    """)
    for section in ("antecedents", "immunizations", "measurements", "notes", "encounters"):
        op.execute(f"ALTER TABLE nightingale.account_memberships DROP COLUMN {section}_access")
