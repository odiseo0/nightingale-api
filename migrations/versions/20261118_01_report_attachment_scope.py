"""Keep diagnostic report attachments inside the same account and patient."""

from alembic import op

revision = "20261118_01"
down_revision = "20261117_07"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$
        DECLARE missing_count bigint; cross_scope_count bigint;
        BEGIN
            SELECT count(*) FILTER (WHERE a.id IS NULL),
                   count(*) FILTER (WHERE a.id IS NOT NULL
                       AND (a.account_id,a.patient_id) IS DISTINCT FROM (r.account_id,r.patient_id))
            INTO missing_count,cross_scope_count
            FROM nightingale.diagnostic_reports r
            LEFT JOIN nightingale.report_attachments a ON a.id=r.attachment_id
            WHERE r.attachment_id IS NOT NULL;
            IF missing_count>0 OR cross_scope_count>0 THEN
                RAISE EXCEPTION 'Invalid report attachments: missing=%, cross_scope=%',
                    missing_count,cross_scope_count USING ERRCODE='23503';
            END IF;
        END; $$
    """)
    op.execute("""
        ALTER TABLE nightingale.diagnostic_reports
        ADD CONSTRAINT diagnostic_reports_attachment_scope_fk
        FOREIGN KEY (account_id,attachment_id,patient_id)
        REFERENCES nightingale.report_attachments(account_id,id,patient_id)
        ON DELETE RESTRICT
    """)


def downgrade():
    op.execute("""
        ALTER TABLE nightingale.diagnostic_reports
        DROP CONSTRAINT diagnostic_reports_attachment_scope_fk
    """)
