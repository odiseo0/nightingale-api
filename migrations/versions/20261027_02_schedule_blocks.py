"""Absolute blocks with stable global or account scope."""

from alembic import op

revision = "20261027_02"
down_revision = "20261027_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.schedule_blocks (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            professional_id uuid NOT NULL REFERENCES nightingale.professionals(id) ON DELETE RESTRICT,
            account_id uuid,
            starts_at timestamptz NOT NULL CHECK (isfinite(starts_at)),
            ends_at timestamptz NOT NULL CHECK (isfinite(ends_at) AND ends_at>starts_at),
            reason_code text NOT NULL CHECK (reason_code IN ('vacation','administrative','unavailable')),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            FOREIGN KEY (account_id,professional_id) REFERENCES nightingale.account_professionals(account_id,professional_id) ON DELETE RESTRICT
        )
    """)
    op.execute("CREATE INDEX ix_schedule_blocks_professional ON nightingale.schedule_blocks(professional_id,starts_at)")
    op.execute("CREATE INDEX ix_schedule_blocks_account ON nightingale.schedule_blocks(account_id,professional_id,starts_at)")
    op.execute("""
        CREATE FUNCTION nightingale.guard_schedule_block() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF (NEW.id,NEW.account_id,NEW.professional_id,NEW.created_at) IS DISTINCT FROM
                (OLD.id,OLD.account_id,OLD.professional_id,OLD.created_at) OR
                NEW.version<>OLD.version+1 OR NEW.updated_at<OLD.updated_at THEN
                RAISE EXCEPTION 'Block references, times or version is invalid' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_schedule_block BEFORE UPDATE ON nightingale.schedule_blocks FOR EACH ROW EXECUTE FUNCTION nightingale.guard_schedule_block()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_schedule_block() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.schedule_blocks TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.schedule_blocks")
    op.execute("DROP FUNCTION nightingale.guard_schedule_block()")
