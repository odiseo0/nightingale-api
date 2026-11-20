"""Recover current report and specialty entries in the clinical timeline."""

from alembic import op

revision = "20261118_03"
down_revision = "20261118_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO nightingale.patient_clinical_timeline (
            account_id,patient_id,entry_type,entry_id,source_section,
            occurred_at,occurrence_date,date_precision,sort_key,accepted_at,
            entity_version,record_status
        )
        SELECT account_id,patient_id,'diagnostic_report',id,'diagnostic_reports',
            CASE WHEN sample_date IS NULL AND issued_date IS NULL THEN updated_at END,
            COALESCE(sample_date,issued_date),
            CASE WHEN COALESCE(sample_date,issued_date) IS NULL THEN 'reference'
                WHEN length(COALESCE(sample_date,issued_date))=4 THEN 'year'
                WHEN length(COALESCE(sample_date,issued_date))=7 THEN 'month'
                ELSE 'day' END,
            COALESCE(sample_date,issued_date,updated_at::text),updated_at,version,record_status
        FROM nightingale.diagnostic_reports
        ON CONFLICT (account_id,patient_id,entry_type,entry_id) DO UPDATE SET
            occurred_at=EXCLUDED.occurred_at,occurrence_date=EXCLUDED.occurrence_date,
            date_precision=EXCLUDED.date_precision,sort_key=EXCLUDED.sort_key,
            accepted_at=EXCLUDED.accepted_at,entity_version=EXCLUDED.entity_version,
            record_status=EXCLUDED.record_status
    """)
    op.execute("""
        INSERT INTO nightingale.patient_clinical_timeline (
            account_id,patient_id,entry_type,entry_id,source_section,
            occurred_at,occurrence_date,date_precision,sort_key,accepted_at,
            entity_version,record_status
        )
        SELECT account_id,patient_id,'specialty_record',id,'specialty_templates',
            recorded_at,NULL,'instant',recorded_at::text,updated_at,version,record_status
        FROM nightingale.specialty_records
        ON CONFLICT (account_id,patient_id,entry_type,entry_id) DO UPDATE SET
            occurred_at=EXCLUDED.occurred_at,occurrence_date=EXCLUDED.occurrence_date,
            date_precision=EXCLUDED.date_precision,sort_key=EXCLUDED.sort_key,
            accepted_at=EXCLUDED.accepted_at,entity_version=EXCLUDED.entity_version,
            record_status=EXCLUDED.record_status
    """)


def downgrade():
    op.execute("""
        DELETE FROM nightingale.patient_clinical_timeline
        WHERE entry_type IN ('diagnostic_report','specialty_record')
    """)
