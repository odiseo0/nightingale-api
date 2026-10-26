"""Directed invitations with atomic membership and receipt references."""

from alembic import op

revision = "20261026_02"
down_revision = "20261026_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.account_invitations (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            invitee_user_id uuid NOT NULL REFERENCES nightingale.app_users(id) ON DELETE RESTRICT,
            created_by_user_id uuid NOT NULL,
            status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','revoked')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            expires_at timestamptz NOT NULL CHECK (isfinite(expires_at) AND expires_at=created_at+interval '72 hours'),
            accepted_at timestamptz,
            accepted_operation_id uuid,
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,invitee_user_id,accepted_operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
            CHECK ((status='accepted' AND accepted_at IS NOT NULL AND accepted_operation_id IS NOT NULL
                AND isfinite(accepted_at) AND accepted_at>=created_at AND accepted_at<=updated_at AND accepted_at<expires_at
                AND uuid_extract_version(accepted_operation_id) IS NOT DISTINCT FROM 7)
                OR (status IN ('pending','revoked') AND accepted_at IS NULL AND accepted_operation_id IS NULL))
        )
    """)
    for name, columns in (
        ("account", "account_id,status,id"), ("recipient", "invitee_user_id,status,id"),
        ("creator", "account_id,created_by_user_id"), ("receipt", "account_id,invitee_user_id,accepted_operation_id"),
    ):
        op.execute(f"CREATE INDEX ix_account_invitations_{name} ON nightingale.account_invitations({columns})")
    op.execute("""
        CREATE FUNCTION nightingale.guard_invitation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF (NEW.id,NEW.account_id,NEW.invitee_user_id,NEW.created_by_user_id,NEW.created_at,NEW.expires_at)
                IS DISTINCT FROM (OLD.id,OLD.account_id,OLD.invitee_user_id,OLD.created_by_user_id,OLD.created_at,OLD.expires_at)
                OR OLD.status<>'pending' OR NEW.version<>OLD.version+1 OR NEW.updated_at<OLD.updated_at THEN
                RAISE EXCEPTION 'Invitation identity and terminal state are immutable' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_invitation BEFORE UPDATE ON nightingale.account_invitations FOR EACH ROW EXECUTE FUNCTION nightingale.guard_invitation()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_invitation() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.account_invitations TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.account_invitations")
    op.execute("DROP FUNCTION nightingale.guard_invitation()")
