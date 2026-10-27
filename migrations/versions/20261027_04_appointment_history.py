"""Deferred history agreement, contiguous versions and immutable past entries."""

from alembic import op

revision = "20261027_04"
down_revision = "20261027_03"
branch_labels = None
depends_on = None


def upgrade():
    # Constraint triggers validate the final transaction state, including history.
    # https://www.postgresql.org/docs/18/sql-createtrigger.html
    op.execute("""
        CREATE FUNCTION nightingale.validate_appointment_history(target uuid, entry_version integer)
        RETURNS void LANGUAGE plpgsql AS $$
        DECLARE
            a nightingale.appointments;
            h nightingale.appointment_histories;
            first_entry nightingale.appointment_histories;
            latest nightingale.appointment_histories;
            previous nightingale.appointment_histories;
            entry_count bigint;
            first_version integer;
            last_version integer;
        BEGIN
            SELECT * INTO a FROM nightingale.appointments WHERE id=target FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Missing appointment' USING ERRCODE='23514';
            END IF;
            SELECT count(*),min(version),max(version) INTO entry_count,first_version,last_version
                FROM nightingale.appointment_histories WHERE appointment_id=target;
            IF entry_count<>a.version OR first_version IS DISTINCT FROM 1 OR last_version IS DISTINCT FROM a.version THEN
                RAISE EXCEPTION 'History versions are not contiguous' USING ERRCODE='23514';
            END IF;
            SELECT * INTO latest FROM nightingale.appointment_histories WHERE appointment_id=target AND version=a.version;
            SELECT * INTO first_entry FROM nightingale.appointment_histories WHERE appointment_id=target AND version=1;
            IF (a.account_id,a.status,a.starts_at,a.ends_at,a.confirmed_at,a.responsible_contact_id,
                a.service_name_snapshot,a.offered_duration_minutes_snapshot,a.professional_name_snapshot,
                a.location_name_snapshot,a.location_address_snapshot,a.location_country_snapshot,
                a.location_state_snapshot,a.location_city_snapshot,a.time_zone_snapshot,a.updated_at,a.created_at)
                IS DISTINCT FROM
               (latest.account_id,latest.status,latest.starts_at,latest.ends_at,latest.confirmed_at,latest.responsible_contact_id,
                latest.service_name_snapshot,latest.offered_duration_minutes_snapshot,latest.professional_name_snapshot,
                latest.location_name_snapshot,latest.location_address_snapshot,latest.location_country_snapshot,
                latest.location_state_snapshot,latest.location_city_snapshot,latest.time_zone_snapshot,latest.changed_at,first_entry.changed_at) THEN
                RAISE EXCEPTION 'Current appointment differs from history' USING ERRCODE='23514';
            END IF;
            SELECT * INTO h FROM nightingale.appointment_histories WHERE appointment_id=target AND version=entry_version;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'Missing history entry' USING ERRCODE='23514';
            END IF;
            IF (h.account_id,h.responsible_contact_id,h.service_name_snapshot,h.offered_duration_minutes_snapshot,
                h.professional_name_snapshot,h.location_name_snapshot,h.location_address_snapshot,
                h.location_country_snapshot,h.location_state_snapshot,h.location_city_snapshot,h.time_zone_snapshot)
                IS DISTINCT FROM
               (a.account_id,first_entry.responsible_contact_id,first_entry.service_name_snapshot,first_entry.offered_duration_minutes_snapshot,
                first_entry.professional_name_snapshot,first_entry.location_name_snapshot,first_entry.location_address_snapshot,
                first_entry.location_country_snapshot,first_entry.location_state_snapshot,first_entry.location_city_snapshot,first_entry.time_zone_snapshot) THEN
                RAISE EXCEPTION 'History references or agreed values changed' USING ERRCODE='23514';
            END IF;
            IF h.actor_kind='contact' AND NOT EXISTS (
                SELECT FROM nightingale.patient_contact_relationships
                WHERE account_id=a.account_id AND patient_id=a.patient_id AND contact_person_id=h.actor_contact_person_id
            ) THEN
                RAISE EXCEPTION 'History actor has no patient relationship' USING ERRCODE='23514';
            END IF;
            IF h.version=1 THEN
                IF h.action<>'created' OR h.status<>'scheduled' OR h.confirmed_at IS NOT NULL OR h.actor_kind<>'staff' THEN
                    RAISE EXCEPTION 'Invalid first history entry' USING ERRCODE='23514';
                END IF;
                RETURN;
            END IF;
            SELECT * INTO previous FROM nightingale.appointment_histories WHERE appointment_id=target AND version=h.version-1;
            IF NOT FOUND OR previous.status NOT IN ('scheduled','confirmed') OR h.changed_at<previous.changed_at THEN
                RAISE EXCEPTION 'Invalid history predecessor' USING ERRCODE='23514';
            END IF;
            IF h.action='rescheduled' THEN
                IF h.status<>'scheduled' OR h.confirmed_at IS NOT NULL
                    OR h.ends_at-h.starts_at<>previous.ends_at-previous.starts_at
                    OR (h.starts_at,h.ends_at) IS NOT DISTINCT FROM (previous.starts_at,previous.ends_at) THEN
                    RAISE EXCEPTION 'Invalid reschedule history' USING ERRCODE='23514';
                END IF;
            ELSIF h.action='confirmed' THEN
                IF previous.status<>'scheduled' OR h.status<>'confirmed' OR h.confirmed_at IS DISTINCT FROM h.changed_at
                    OR (h.starts_at,h.ends_at) IS DISTINCT FROM (previous.starts_at,previous.ends_at) THEN
                    RAISE EXCEPTION 'Invalid confirmation history' USING ERRCODE='23514';
                END IF;
            ELSIF h.action IN ('cancelled','completed','no_show') THEN
                IF h.status<>h.action OR (h.starts_at,h.ends_at,h.confirmed_at) IS DISTINCT FROM
                    (previous.starts_at,previous.ends_at,previous.confirmed_at)
                    OR (h.action IN ('completed','no_show') AND h.changed_at<h.starts_at) THEN
                    RAISE EXCEPTION 'Invalid terminal history' USING ERRCODE='23514';
                END IF;
            ELSE
                RAISE EXCEPTION 'Invalid history action' USING ERRCODE='23514';
            END IF;
        END; $$
    """)
    op.execute("""
        CREATE FUNCTION nightingale.check_appointment_history() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_TABLE_NAME='appointments' THEN
                PERFORM nightingale.validate_appointment_history(NEW.id,NEW.version);
            ELSE
                PERFORM nightingale.validate_appointment_history(NEW.appointment_id,NEW.version);
            END IF;
            RETURN NULL;
        END; $$
    """)
    for table in ("appointments", "appointment_histories"):
        op.execute(f"CREATE CONSTRAINT TRIGGER check_appointment_history AFTER INSERT OR UPDATE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_appointment_history()")
    op.execute("""
        CREATE FUNCTION nightingale.reject_history_rewrite() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Appointment history is immutable' USING ERRCODE='23514';
        END; $$
    """)
    op.execute("CREATE TRIGGER reject_history_rewrite BEFORE UPDATE OR DELETE ON nightingale.appointment_histories FOR EACH ROW EXECUTE FUNCTION nightingale.reject_history_rewrite()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_appointment_history() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION nightingale.reject_history_rewrite() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION nightingale.validate_appointment_history(uuid,integer) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION nightingale.validate_appointment_history(uuid,integer) TO nightingale_runtime")
    # Validate existing entries too when upgrading a database that ran T22.
    op.execute("SELECT nightingale.validate_appointment_history(a.id,h.version) FROM nightingale.appointments a LEFT JOIN nightingale.appointment_histories h ON h.appointment_id=a.id")


def downgrade():
    op.execute("DROP TRIGGER reject_history_rewrite ON nightingale.appointment_histories")
    for table in ("appointments", "appointment_histories"):
        op.execute(f"DROP TRIGGER check_appointment_history ON nightingale.{table}")
    op.execute("DROP FUNCTION nightingale.reject_history_rewrite()")
    op.execute("DROP FUNCTION nightingale.check_appointment_history()")
    op.execute("DROP FUNCTION nightingale.validate_appointment_history(uuid,integer)")
