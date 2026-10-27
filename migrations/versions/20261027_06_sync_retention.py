"""Enforce 90-day group retention and keep minimal receipts after cleanup."""

from alembic import op

revision = "20261027_06"
down_revision = "20261027_05"
branch_labels = None
depends_on = None

JOURNAL_CHECK = """
    CREATE OR REPLACE FUNCTION nightingale.check_operation_journal() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE target uuid; head nightingale.account_sync_heads; receipt nightingale.operation_receipts;
    BEGIN
        target := COALESCE(NEW.account_id,OLD.account_id);
        SELECT * INTO head FROM nightingale.account_sync_heads WHERE account_id=target;
        IF NOT FOUND THEN RETURN NULL; END IF;
        IF (SELECT count(DISTINCT sequence) FROM nightingale.change_log WHERE account_id=target)
            <>head.last_sequence-head.retained_from_sequence+1 OR EXISTS (
            SELECT FROM nightingale.change_log WHERE account_id=target
            GROUP BY sequence HAVING sequence<head.retained_from_sequence OR sequence>head.last_sequence
                OR min(ordinal)<>1 OR max(ordinal)<>max(group_size) OR count(*)<>max(group_size)
                OR min(group_size)<>max(group_size) OR count(DISTINCT group_id)<>1
                OR count(DISTINCT (source_account_id,actor_user_id,operation_id,accepted_at))<>1
        ) OR EXISTS (
            SELECT FROM nightingale.change_log c JOIN nightingale.operation_receipts r
            ON (r.account_id,r.actor_user_id,r.operation_id)=(c.source_account_id,c.actor_user_id,c.operation_id)
            WHERE c.account_id=target AND (r.status<>'accepted' OR c.accepted_at<>r.completed_at)
        ) THEN
            RAISE EXCEPTION 'Journal group or boundary is incomplete' USING ERRCODE='23514';
        END IF;
        IF TG_TABLE_NAME='operation_receipts' THEN
            SELECT * INTO receipt FROM nightingale.operation_receipts
            WHERE (account_id,actor_user_id,operation_id)=(NEW.account_id,NEW.actor_user_id,NEW.operation_id);
            IF NOT EXISTS (SELECT FROM nightingale.audit_events a WHERE
                (a.account_id,a.actor_user_id,a.operation_id)=(receipt.account_id,receipt.actor_user_id,receipt.operation_id)
                AND a.outcome=receipt.status AND a.action=receipt.action) OR
                (receipt.status='accepted' AND ({require_changes}) AND NOT EXISTS (SELECT FROM nightingale.change_log c WHERE
                    (c.source_account_id,c.actor_user_id,c.operation_id)=(receipt.account_id,receipt.actor_user_id,receipt.operation_id))) THEN
                RAISE EXCEPTION 'Receipt requires its audit and accepted changes' USING ERRCODE='23514';
            END IF;
        END IF;
        RETURN NULL;
    END; $$
"""


def upgrade():
    # Inserts still require their journal, including historical test fixtures.
    # Only an update of an old receipt can outlive its retained download groups.
    op.execute(JOURNAL_CHECK.format(require_changes="TG_OP='INSERT' OR receipt.completed_at>clock_timestamp()-interval '90 days'"))
    op.execute("""
        CREATE FUNCTION nightingale.guard_change_retention() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.accepted_at>clock_timestamp()-interval '90 days' THEN
                RAISE EXCEPTION 'Confirmed groups must remain for 90 days' USING ERRCODE='23514';
            END IF;
            RETURN OLD;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_change_retention BEFORE DELETE ON nightingale.change_log FOR EACH ROW EXECUTE FUNCTION nightingale.guard_change_retention()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_change_retention() FROM PUBLIC")


def downgrade():
    op.execute("DROP TRIGGER guard_change_retention ON nightingale.change_log")
    op.execute("DROP FUNCTION nightingale.guard_change_retention()")
    op.execute(JOURNAL_CHECK.format(require_changes="true"))
