"""Clinical section access and explicit snapshot scopes."""

from alembic import op

revision = "20261115_01"
down_revision = "20261028_01"
branch_labels = None
depends_on = None


def upgrade():
    for column in ("clinical_profile_access", "conditions_access", "allergies_access"):
        op.execute(f"""
            ALTER TABLE nightingale.account_memberships
            ADD COLUMN {column} text NOT NULL DEFAULT 'read_write'
            CHECK ({column} IN ('none','read','read_write'))
        """)
    op.execute("ALTER TABLE nightingale.sync_snapshots ADD COLUMN clinical_sections jsonb NOT NULL DEFAULT '[]'")
    op.execute("""
        CREATE FUNCTION nightingale.valid_clinical_sections(value jsonb) RETURNS boolean
        LANGUAGE sql IMMUTABLE AS $$
            SELECT jsonb_typeof(value)='array'
                AND value <@ '["profile","conditions","allergies"]'::jsonb
                AND (SELECT count(*)=count(DISTINCT item)
                    FROM jsonb_array_elements_text(value) AS section(item));
        $$
    """)
    op.execute("REVOKE ALL ON FUNCTION nightingale.valid_clinical_sections(jsonb) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION nightingale.valid_clinical_sections(jsonb) TO nightingale_runtime")
    op.execute("""
        ALTER TABLE nightingale.sync_snapshots
        ADD CONSTRAINT sync_snapshots_clinical_sections_check
        CHECK (nightingale.valid_clinical_sections(clinical_sections))
    """)
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute("""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN ('members','owner','clinical_profile','clinical_conditions','clinical_allergies'))
    """)


def downgrade():
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute("""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check CHECK (audience IN ('members','owner'))
    """)
    op.execute("ALTER TABLE nightingale.sync_snapshots DROP COLUMN clinical_sections")
    op.execute("DROP FUNCTION nightingale.valid_clinical_sections(jsonb)")
    op.execute("ALTER TABLE nightingale.account_memberships DROP COLUMN allergies_access")
    op.execute("ALTER TABLE nightingale.account_memberships DROP COLUMN conditions_access")
    op.execute("ALTER TABLE nightingale.account_memberships DROP COLUMN clinical_profile_access")
