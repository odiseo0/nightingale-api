"""Backfill current stage-one entries into the clinical timeline."""

from alembic import op

revision = "20261116_10"
down_revision = "20261116_09"
branch_labels = None
depends_on = None


def upgrade():
    for table, entry_type, section in (
        ("patient_conditions", "condition", "conditions"),
        ("patient_allergy_intolerances", "allergy_intolerance", "allergies"),
    ):
        op.execute(f"""
            INSERT INTO nightingale.patient_clinical_timeline (
                account_id,patient_id,entry_type,entry_id,source_section,
                occurred_at,occurrence_date,date_precision,sort_key,accepted_at,
                entity_version,record_status
            )
            SELECT account_id,patient_id,'{entry_type}',id,'{section}',
                CASE WHEN onset_date IS NULL THEN updated_at END,
                onset_date,
                CASE WHEN onset_date IS NULL THEN 'reference'
                    WHEN length(onset_date)=4 THEN 'year'
                    WHEN length(onset_date)=7 THEN 'month' ELSE 'day' END,
                COALESCE(onset_date,updated_at::text),updated_at,version,
                CASE WHEN verification_status='entered-in-error' THEN 'entered-in-error' ELSE 'valid' END
            FROM nightingale.{table}
            ON CONFLICT (account_id,patient_id,entry_type,entry_id) DO UPDATE SET
                occurred_at=EXCLUDED.occurred_at,occurrence_date=EXCLUDED.occurrence_date,
                date_precision=EXCLUDED.date_precision,sort_key=EXCLUDED.sort_key,
                accepted_at=EXCLUDED.accepted_at,entity_version=EXCLUDED.entity_version,
                record_status=EXCLUDED.record_status
        """)


def downgrade():
    op.execute("DELETE FROM nightingale.patient_clinical_timeline WHERE entry_type IN ('condition','allergy_intolerance')")
