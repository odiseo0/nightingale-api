"""Weekly local-time rules, with explicit open-ended uniqueness."""

from alembic import op

revision = "20261026_08"
down_revision = "20261026_07"
branch_labels = None
depends_on = None


def upgrade():
    # NULLS NOT DISTINCT also protects open-ended duplicates in direct SQL.
    # https://www.postgresql.org/docs/18/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS
    op.execute("""
        CREATE TABLE nightingale.schedule_rules (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            professional_id uuid NOT NULL,
            iso_weekday smallint NOT NULL CHECK (iso_weekday BETWEEN 1 AND 7),
            local_start_minute smallint NOT NULL CHECK (local_start_minute BETWEEN 0 AND 1439),
            local_end_minute smallint NOT NULL CHECK (local_end_minute BETWEEN 1 AND 1440 AND local_end_minute>local_start_minute),
            valid_from date NOT NULL CHECK (isfinite(valid_from)),
            valid_until date CHECK (isfinite(valid_until) AND valid_until>=valid_from),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            FOREIGN KEY (account_id,professional_id) REFERENCES nightingale.account_professionals(account_id,professional_id) ON DELETE RESTRICT,
            UNIQUE NULLS NOT DISTINCT (account_id,professional_id,iso_weekday,local_start_minute,local_end_minute,valid_from,valid_until)
        )
    """)
    op.execute("CREATE INDEX ix_schedule_rules_professional ON nightingale.schedule_rules(professional_id,account_id,iso_weekday)")
    op.execute("""
        CREATE FUNCTION nightingale.guard_schedule_rule() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF (NEW.id,NEW.account_id,NEW.professional_id,NEW.created_at) IS DISTINCT FROM
                (OLD.id,OLD.account_id,OLD.professional_id,OLD.created_at) OR
                NEW.version<>OLD.version+1 OR NEW.updated_at<OLD.updated_at THEN
                RAISE EXCEPTION 'Rule references, times or version is invalid' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_schedule_rule BEFORE UPDATE ON nightingale.schedule_rules FOR EACH ROW EXECUTE FUNCTION nightingale.guard_schedule_rule()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_schedule_rule() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.schedule_rules TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.schedule_rules")
    op.execute("DROP FUNCTION nightingale.guard_schedule_rule()")
