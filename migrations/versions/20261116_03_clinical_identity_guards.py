"""Stable account, record and patient identity for clinical rows."""

from alembic import op

revision = "20261116_03"
down_revision = "20261116_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE FUNCTION nightingale.guard_clinical_identity() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.account_id IS DISTINCT FROM OLD.account_id
                OR NEW.patient_id IS DISTINCT FROM OLD.patient_id THEN
                RAISE EXCEPTION 'Clinical identity is immutable' USING ERRCODE='23514';
            END IF;
            IF TG_TABLE_NAME IN ('patient_conditions','patient_allergy_intolerances') THEN
                IF NEW.id IS DISTINCT FROM OLD.id THEN
                    RAISE EXCEPTION 'Clinical identity is immutable' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NEW;
        END; $$
    """)
    for table in (
        "patient_clinical_profiles",
        "patient_conditions",
        "patient_allergy_intolerances",
    ):
        op.execute(f"""
            CREATE TRIGGER guard_clinical_identity BEFORE UPDATE ON nightingale.{table}
            FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_identity()
        """)


def downgrade():
    for table in (
        "patient_allergy_intolerances",
        "patient_conditions",
        "patient_clinical_profiles",
    ):
        op.execute(f"DROP TRIGGER guard_clinical_identity ON nightingale.{table}")
    op.execute("DROP FUNCTION nightingale.guard_clinical_identity()")
