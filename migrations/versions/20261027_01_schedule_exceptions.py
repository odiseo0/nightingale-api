"""One retained exception per professional, account and local date."""

from alembic import op

revision = "20261027_01"
down_revision = "20261026_08"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.schedule_exceptions (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            professional_id uuid NOT NULL,
            local_date date NOT NULL CHECK (isfinite(local_date)),
            kind text NOT NULL CHECK (kind IN ('closed','replacement')),
            local_start_minute smallint,
            local_end_minute smallint,
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            FOREIGN KEY (account_id,professional_id) REFERENCES nightingale.account_professionals(account_id,professional_id) ON DELETE RESTRICT,
            UNIQUE (account_id,professional_id,local_date),
            CHECK ((kind='closed' AND local_start_minute IS NULL AND local_end_minute IS NULL)
                OR (kind='replacement' AND local_start_minute IS NOT NULL AND local_end_minute IS NOT NULL
                    AND local_start_minute BETWEEN 0 AND 1439 AND local_end_minute BETWEEN 1 AND 1440
                    AND local_start_minute<local_end_minute))
        )
    """)
    op.execute("CREATE INDEX ix_schedule_exceptions_professional ON nightingale.schedule_exceptions(professional_id,local_date,account_id)")
    op.execute("""
        CREATE FUNCTION nightingale.guard_schedule_exception() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF (NEW.id,NEW.account_id,NEW.professional_id,NEW.created_at) IS DISTINCT FROM
                (OLD.id,OLD.account_id,OLD.professional_id,OLD.created_at) OR
                NEW.version<>OLD.version+1 OR NEW.updated_at<OLD.updated_at THEN
                RAISE EXCEPTION 'Exception references, times or version is invalid' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_schedule_exception BEFORE UPDATE ON nightingale.schedule_exceptions FOR EACH ROW EXECUTE FUNCTION nightingale.guard_schedule_exception()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_schedule_exception() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.schedule_exceptions TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.schedule_exceptions")
    op.execute("DROP FUNCTION nightingale.guard_schedule_exception()")
