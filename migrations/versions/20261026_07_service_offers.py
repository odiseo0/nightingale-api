"""Account-scoped offers of a professional's own service."""

from alembic import op

revision = "20261026_07"
down_revision = "20261026_06"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.professional_services (
            account_id uuid NOT NULL,
            professional_id uuid NOT NULL,
            service_id uuid NOT NULL,
            duration_minutes_override integer CHECK (duration_minutes_override BETWEEN 1 AND 1440),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            PRIMARY KEY (account_id,professional_id,service_id),
            FOREIGN KEY (account_id,professional_id) REFERENCES nightingale.account_professionals(account_id,professional_id) ON DELETE RESTRICT,
            FOREIGN KEY (professional_id,service_id) REFERENCES nightingale.services(professional_id,id) ON DELETE RESTRICT
        )
    """)
    op.execute("CREATE INDEX ix_professional_services_catalog ON nightingale.professional_services(professional_id,service_id,account_id)")
    op.execute("""
        CREATE FUNCTION nightingale.guard_service_offer() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF (NEW.account_id,NEW.professional_id,NEW.service_id,NEW.created_at) IS DISTINCT FROM
                (OLD.account_id,OLD.professional_id,OLD.service_id,OLD.created_at) OR
                NEW.version<>OLD.version+1 OR NEW.updated_at<OLD.updated_at THEN
                RAISE EXCEPTION 'Offer references, times or version is invalid' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_service_offer BEFORE UPDATE ON nightingale.professional_services FOR EACH ROW EXECUTE FUNCTION nightingale.guard_service_offer()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_service_offer() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.professional_services TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.professional_services")
    op.execute("DROP FUNCTION nightingale.guard_service_offer()")
