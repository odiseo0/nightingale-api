"""Transactional hints and short stream leases shared by API processes."""

from alembic import op

revision = "20261028_01"
down_revision = "20261027_06"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.sync_stream_leases (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL, user_id uuid NOT NULL, device_id uuid NOT NULL,
            expires_at timestamptz NOT NULL CHECK (isfinite(expires_at)),
            FOREIGN KEY (account_id,user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (device_id,user_id) REFERENCES nightingale.devices(id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,device_id) REFERENCES nightingale.account_device_accesses(account_id,device_id) ON DELETE RESTRICT
        )
    """)
    op.execute("CREATE INDEX ix_sync_stream_leases_scope ON nightingale.sync_stream_leases(account_id,device_id,expires_at)")
    op.execute("CREATE INDEX ix_sync_stream_leases_user ON nightingale.sync_stream_leases(account_id,user_id)")
    op.execute("CREATE INDEX ix_sync_stream_leases_device ON nightingale.sync_stream_leases(device_id,user_id)")
    op.execute("CREATE INDEX ix_sync_stream_leases_expiry ON nightingale.sync_stream_leases(expires_at)")
    op.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON nightingale.sync_stream_leases TO nightingale_runtime")
    # PostgreSQL delivers this hint only after the surrounding commit succeeds.
    # https://www.postgresql.org/docs/18/sql-notify.html
    op.execute("""
        CREATE FUNCTION nightingale.notify_sync_head() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            PERFORM pg_notify('nightingale_sync', NEW.account_id::text || ':' || NEW.last_sequence::text);
            RETURN NEW;
        END; $$
    """)
    op.execute("""
        CREATE TRIGGER notify_sync_head AFTER UPDATE OF last_sequence,permission_epoch
        ON nightingale.account_sync_heads FOR EACH ROW
        WHEN (OLD.last_sequence IS DISTINCT FROM NEW.last_sequence OR OLD.permission_epoch IS DISTINCT FROM NEW.permission_epoch)
        EXECUTE FUNCTION nightingale.notify_sync_head()
    """)
    op.execute("REVOKE ALL ON FUNCTION nightingale.notify_sync_head() FROM PUBLIC")


def downgrade():
    op.execute("DROP TRIGGER notify_sync_head ON nightingale.account_sync_heads")
    op.execute("DROP FUNCTION nightingale.notify_sync_head()")
    op.execute("DROP TABLE nightingale.sync_stream_leases")
