"""Professional-owned private service catalog."""

from alembic import op

revision = "20261026_06"
down_revision = "20261026_05"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.services (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            professional_id uuid NOT NULL REFERENCES nightingale.professionals(id) ON DELETE RESTRICT,
            name text NOT NULL CHECK (length(btrim(name))>0),
            default_duration_minutes integer NOT NULL CHECK (default_duration_minutes BETWEEN 1 AND 1440),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (professional_id,id)
        )
    """)
    op.execute("CREATE INDEX ix_services_professional_status ON nightingale.services(professional_id,status)")
    op.execute("""
        CREATE FUNCTION nightingale.guard_service_record() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF (NEW.id,NEW.professional_id,NEW.created_at) IS DISTINCT FROM
                (OLD.id,OLD.professional_id,OLD.created_at) OR
                NEW.version<>OLD.version+1 OR NEW.updated_at<OLD.updated_at THEN
                RAISE EXCEPTION 'Service ownership, times or version is invalid' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_service_record BEFORE UPDATE ON nightingale.services FOR EACH ROW EXECUTE FUNCTION nightingale.guard_service_record()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_service_record() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.services TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.services")
    op.execute("DROP FUNCTION nightingale.guard_service_record()")
