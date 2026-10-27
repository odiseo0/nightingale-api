"""Appointments, global occupancy and the first atomic history entry."""

from alembic import op

revision = "20261027_03"
down_revision = "20261027_02"
branch_labels = None
depends_on = None


def upgrade():
    # This revision owns the extension in the dedicated application schema.
    # https://www.postgresql.org/docs/18/rangetypes.html#RANGETYPES-CONSTRAINT
    op.execute("CREATE EXTENSION btree_gist WITH SCHEMA nightingale")
    snapshots = """
        service_name_snapshot text NOT NULL CHECK (btrim(service_name_snapshot)<>''),
        offered_duration_minutes_snapshot integer NOT NULL CHECK (offered_duration_minutes_snapshot BETWEEN 1 AND 1440),
        professional_name_snapshot text NOT NULL CHECK (btrim(professional_name_snapshot)<>''),
        location_name_snapshot text NOT NULL CHECK (btrim(location_name_snapshot)<>''),
        location_address_snapshot text NOT NULL CHECK (btrim(location_address_snapshot)<>''),
        location_country_snapshot text NOT NULL CHECK (location_country_snapshot ~ '^[A-Z]{2}$'),
        location_state_snapshot text NOT NULL CHECK (btrim(location_state_snapshot)<>''),
        location_city_snapshot text NOT NULL CHECK (btrim(location_city_snapshot)<>''),
        time_zone_snapshot text NOT NULL CHECK (btrim(time_zone_snapshot)<>''),
    """
    interval_state = """
        starts_at timestamptz NOT NULL CHECK (isfinite(starts_at) AND date_trunc('minute',starts_at)=starts_at),
        ends_at timestamptz NOT NULL CHECK (isfinite(ends_at) AND date_trunc('minute',ends_at)=ends_at
            AND ends_at-starts_at BETWEEN interval '1 minute' AND interval '1440 minutes'),
        status text NOT NULL CHECK (status IN ('scheduled','confirmed','cancelled','completed','no_show')),
        confirmed_at timestamptz CHECK (isfinite(confirmed_at)),
        responsible_contact_id uuid,
        version integer NOT NULL CHECK (version>0),
        CHECK ((status<>'scheduled' OR confirmed_at IS NULL) AND (status<>'confirmed' OR confirmed_at IS NOT NULL)),
    """
    op.execute(f"""
        CREATE TABLE nightingale.appointments (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            professional_id uuid NOT NULL,
            service_id uuid NOT NULL,
            {interval_state}
            {snapshots}
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            CHECK (confirmed_at IS NULL OR confirmed_at BETWEEN created_at AND updated_at),
            UNIQUE (account_id,id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,professional_id,service_id) REFERENCES nightingale.professional_services(account_id,professional_id,service_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,patient_id,responsible_contact_id) REFERENCES nightingale.patient_contact_relationships(account_id,patient_id,contact_person_id) ON DELETE RESTRICT,
            EXCLUDE USING gist (
                professional_id nightingale.gist_uuid_ops WITH =,
                tstzrange(starts_at,ends_at,'[)') WITH &&
            ) WHERE (status IN ('scheduled','confirmed','completed','no_show'))
        )
    """)
    op.execute(f"""
        CREATE TABLE nightingale.appointment_histories (
            appointment_id uuid NOT NULL,
            account_id uuid NOT NULL,
            {interval_state}
            {snapshots}
            action text NOT NULL CHECK (action IN ('created','confirmed','rescheduled','cancelled','completed','no_show')),
            actor_kind text NOT NULL CHECK (actor_kind IN ('staff','patient','contact')),
            actor_user_id uuid,
            actor_contact_person_id uuid,
            change_reason text CHECK (btrim(change_reason)<>''),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at) AND (confirmed_at IS NULL OR confirmed_at<=changed_at)),
            PRIMARY KEY (appointment_id,version),
            UNIQUE (account_id,appointment_id,version),
            FOREIGN KEY (account_id,appointment_id) REFERENCES nightingale.appointments(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,responsible_contact_id) REFERENCES nightingale.contact_people(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_contact_person_id) REFERENCES nightingale.contact_people(account_id,id) ON DELETE RESTRICT,
            CHECK ((actor_kind='staff' AND actor_user_id IS NOT NULL AND actor_contact_person_id IS NULL)
                OR (actor_kind='contact' AND actor_user_id IS NULL AND actor_contact_person_id IS NOT NULL)
                OR (actor_kind='patient' AND actor_user_id IS NULL AND actor_contact_person_id IS NULL))
        )
    """)
    op.execute("""
        ALTER TABLE nightingale.appointments ADD CONSTRAINT current_appointment_history
            FOREIGN KEY (account_id,id,version) REFERENCES nightingale.appointment_histories(account_id,appointment_id,version)
            DEFERRABLE INITIALLY DEFERRED
    """)
    for table, columns in (
        ("appointments", "account_id,starts_at,id"),
        ("appointments", "professional_id,starts_at,id"),
        ("appointments", "account_id,patient_id,starts_at,id"),
        ("appointments", "account_id,professional_id,service_id"),
        ("appointments", "account_id,patient_id,responsible_contact_id"),
        ("appointment_histories", "account_id,actor_user_id"),
        ("appointment_histories", "account_id,actor_contact_person_id"),
        ("appointment_histories", "account_id,responsible_contact_id"),
    ):
        op.execute(f"CREATE INDEX ix_{table}_{columns.replace(',', '_')} ON nightingale.{table}({columns})")
    op.execute("""
        CREATE FUNCTION nightingale.guard_appointment() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_timezone_names WHERE name=NEW.time_zone_snapshot) THEN
                RAISE EXCEPTION 'Unknown time zone' USING ERRCODE='23514';
            END IF;
            IF TG_OP='UPDATE' AND (
                (NEW.id,NEW.account_id,NEW.patient_id,NEW.professional_id,NEW.service_id,NEW.created_at) IS DISTINCT FROM
                (OLD.id,OLD.account_id,OLD.patient_id,OLD.professional_id,OLD.service_id,OLD.created_at)
                OR NEW.version<>OLD.version+1 OR NEW.updated_at<OLD.updated_at
            ) THEN
                RAISE EXCEPTION 'Appointment references, times or version is invalid' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_appointment BEFORE INSERT OR UPDATE ON nightingale.appointments FOR EACH ROW EXECUTE FUNCTION nightingale.guard_appointment()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_appointment() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.appointments TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.appointment_histories TO nightingale_runtime")


def downgrade():
    op.execute("ALTER TABLE nightingale.appointments DROP CONSTRAINT current_appointment_history")
    op.execute("DROP TABLE nightingale.appointment_histories")
    op.execute("DROP TABLE nightingale.appointments")
    op.execute("DROP FUNCTION nightingale.guard_appointment()")
    op.execute("DROP EXTENSION btree_gist")
