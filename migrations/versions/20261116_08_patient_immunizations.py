"""Patient immunizations with partial dates and immutable history."""

from alembic import op

revision = "20261116_08"
down_revision = "20261116_07"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.patient_immunizations (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            vaccine_name text NOT NULL CHECK (btrim(vaccine_name)<>''),
            occurrence_date text NOT NULL CHECK (occurrence_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            record_kind text NOT NULL DEFAULT 'unknown' CHECK (record_kind IN ('administered_here','reported','unknown')),
            source_type text NOT NULL DEFAULT 'unknown' CHECK (source_type IN ('patient','related_person','professional','external_document','unknown')),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            product_name text CHECK (product_name IS NULL OR btrim(product_name)<>''),
            dose_description text CHECK (dose_description IS NULL OR btrim(dose_description)<>''),
            lot_number text CHECK (lot_number IS NULL OR btrim(lot_number)<>''),
            route text CHECK (route IS NULL OR btrim(route)<>''),
            body_site text CHECK (body_site IS NULL OR btrim(body_site)<>''),
            location_text text CHECK (location_text IS NULL OR btrim(location_text)<>''),
            administrator_name text CHECK (administrator_name IS NULL OR btrim(administrator_name)<>''),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            created_by_user_id uuid NOT NULL,
            updated_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            CHECK (record_kind<>'administered_here' OR encounter_id IS NOT NULL),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id) REFERENCES nightingale.clinical_encounters(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.patient_immunization_histories (
            account_id uuid NOT NULL,
            id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            vaccine_name text NOT NULL CHECK (btrim(vaccine_name)<>''),
            occurrence_date text NOT NULL CHECK (occurrence_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            record_kind text NOT NULL CHECK (record_kind IN ('administered_here','reported','unknown')),
            source_type text NOT NULL CHECK (source_type IN ('patient','related_person','professional','external_document','unknown')),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            product_name text CHECK (product_name IS NULL OR btrim(product_name)<>''),
            dose_description text CHECK (dose_description IS NULL OR btrim(dose_description)<>''),
            lot_number text CHECK (lot_number IS NULL OR btrim(lot_number)<>''),
            route text CHECK (route IS NULL OR btrim(route)<>''),
            body_site text CHECK (body_site IS NULL OR btrim(body_site)<>''),
            location_text text CHECK (location_text IS NULL OR btrim(location_text)<>''),
            administrator_name text CHECK (administrator_name IS NULL OR btrim(administrator_name)<>''),
            record_status text NOT NULL CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            version integer NOT NULL CHECK (version>0),
            action text NOT NULL CHECK (action IN ('created','updated','invalidated')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,id,version),
            CHECK (record_kind<>'administered_here' OR encounter_id IS NOT NULL),
            FOREIGN KEY (account_id,id) REFERENCES nightingale.patient_immunizations(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("ALTER TABLE nightingale.patient_immunizations ADD CONSTRAINT patient_immunization_current_version FOREIGN KEY (account_id,id,version) REFERENCES nightingale.patient_immunization_histories(account_id,id,version) DEFERRABLE INITIALLY DEFERRED")
    op.execute("CREATE INDEX ix_patient_immunizations_list ON nightingale.patient_immunizations(account_id,patient_id,record_status,occurrence_date,id)")
    op.execute("CREATE INDEX ix_patient_immunizations_encounter ON nightingale.patient_immunizations(account_id,encounter_id,patient_id)")
    op.execute("CREATE INDEX ix_patient_immunization_history_receipt ON nightingale.patient_immunization_histories(account_id,actor_user_id,operation_id)")
    op.execute("""
        CREATE FUNCTION nightingale.check_patient_immunization() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer;
        BEGIN
            SELECT version INTO current_version FROM nightingale.patient_immunizations WHERE account_id=NEW.account_id AND id=NEW.id;
            SELECT count(*),max(version) INTO entries,current_version FROM nightingale.patient_immunization_histories WHERE account_id=NEW.account_id AND id=NEW.id;
            IF current_version IS NULL OR entries<>current_version OR (SELECT count(*) FROM nightingale.patient_immunizations i JOIN nightingale.patient_immunization_histories h ON h.account_id=i.account_id AND h.id=i.id AND h.version=i.version WHERE i.account_id=NEW.account_id AND i.id=NEW.id AND ROW(h.patient_id,h.encounter_id,h.vaccine_name,h.occurrence_date,h.record_kind,h.source_type,h.captured_at_local,h.product_name,h.dose_description,h.lot_number,h.route,h.body_site,h.location_text,h.administrator_name,h.record_status,h.correction_reason) IS NOT DISTINCT FROM ROW(i.patient_id,i.encounter_id,i.vaccine_name,i.occurrence_date,i.record_kind,i.source_type,i.captured_at_local,i.product_name,i.dose_description,i.lot_number,i.route,i.body_site,i.location_text,i.administrator_name,i.record_status,i.correction_reason))<>1 THEN
                RAISE EXCEPTION 'Patient immunization and history disagree' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE CONSTRAINT TRIGGER check_patient_immunization_current AFTER INSERT OR UPDATE ON nightingale.patient_immunizations DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_immunization()")
    op.execute("CREATE CONSTRAINT TRIGGER check_patient_immunization_history AFTER INSERT ON nightingale.patient_immunization_histories DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_immunization()")
    op.execute("CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.patient_immunization_histories FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
    op.execute("CREATE TRIGGER guard_clinical_identity BEFORE UPDATE ON nightingale.patient_immunizations FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_identity()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_patient_immunization() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.patient_immunizations TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.patient_immunization_histories TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.patient_immunizations CASCADE")
    op.execute("DROP TABLE nightingale.patient_immunization_histories")
    op.execute("DROP FUNCTION nightingale.check_patient_immunization()")
