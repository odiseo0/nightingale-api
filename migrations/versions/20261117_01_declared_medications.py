"""Declared medications with source, period precision, review and immutable history."""

from alembic import op

revision = "20261117_01"
down_revision = "20261116_10"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE nightingale.account_memberships
        ADD COLUMN declared_medications_access text NOT NULL DEFAULT 'read_write'
        CHECK (declared_medications_access IN ('none','read','read_write'))
    """)
    op.execute("ALTER TABLE nightingale.operation_receipts DROP CONSTRAINT operation_receipts_clinical_section_check")
    op.execute("""
        ALTER TABLE nightingale.operation_receipts
        ADD CONSTRAINT operation_receipts_clinical_section_check
        CHECK (clinical_section IN (
            'profile','conditions','allergies','encounters','notes',
            'measurements','immunizations','antecedents','declared_medications'
        ))
    """)
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute("""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN (
            'members','owner','clinical_profile','clinical_conditions','clinical_allergies',
            'clinical_encounters','clinical_notes','clinical_measurements',
            'clinical_immunizations','clinical_antecedents','clinical_declared_medications'
        ))
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_clinical_sections(value jsonb) RETURNS boolean
        LANGUAGE sql IMMUTABLE AS $$
            SELECT jsonb_typeof(value)='array'
                AND value <@ '["profile","conditions","allergies","encounters","notes","measurements","immunizations","antecedents","declared_medications"]'::jsonb
                AND (SELECT count(*)=count(DISTINCT item)
                    FROM jsonb_array_elements_text(value) AS section(item));
        $$
    """)
    op.execute("""
        CREATE TABLE nightingale.declared_medications (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            medication_name text NOT NULL CHECK (btrim(medication_name)<>''),
            source_type text NOT NULL CHECK (source_type IN ('patient','caregiver','other_professional','document')),
            start_date text CHECK (start_date IS NULL OR start_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            end_date text CHECK (end_date IS NULL OR end_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            dose_description text CHECK (dose_description IS NULL OR btrim(dose_description)<>''),
            frequency_description text CHECK (frequency_description IS NULL OR btrim(frequency_description)<>''),
            prescriber_name text CHECK (prescriber_name IS NULL OR btrim(prescriber_name)<>''),
            route_description text CHECK (route_description IS NULL OR btrim(route_description)<>''),
            review_status text NOT NULL DEFAULT 'declared' CHECK (review_status IN ('declared','reviewed')),
            reviewed_at timestamptz CHECK (reviewed_at IS NULL OR isfinite(reviewed_at)),
            reviewed_by_user_id uuid,
            captured_at_local timestamptz CHECK (captured_at_local IS NULL OR isfinite(captured_at_local)),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            created_by_user_id uuid NOT NULL,
            updated_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            CHECK (review_status<>'reviewed' OR (reviewed_at IS NOT NULL AND reviewed_by_user_id IS NOT NULL)),
            CHECK (review_status<>'declared' OR (reviewed_at IS NULL AND reviewed_by_user_id IS NULL)),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id) REFERENCES nightingale.clinical_encounters(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,reviewed_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.declared_medication_histories (
            account_id uuid NOT NULL,
            id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            medication_name text NOT NULL CHECK (btrim(medication_name)<>''),
            source_type text NOT NULL CHECK (source_type IN ('patient','caregiver','other_professional','document')),
            start_date text CHECK (start_date IS NULL OR start_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            end_date text CHECK (end_date IS NULL OR end_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            dose_description text CHECK (dose_description IS NULL OR btrim(dose_description)<>''),
            frequency_description text CHECK (frequency_description IS NULL OR btrim(frequency_description)<>''),
            prescriber_name text CHECK (prescriber_name IS NULL OR btrim(prescriber_name)<>''),
            route_description text CHECK (route_description IS NULL OR btrim(route_description)<>''),
            review_status text NOT NULL CHECK (review_status IN ('declared','reviewed')),
            reviewed_at timestamptz CHECK (reviewed_at IS NULL OR isfinite(reviewed_at)),
            reviewed_by_user_id uuid,
            captured_at_local timestamptz CHECK (captured_at_local IS NULL OR isfinite(captured_at_local)),
            record_status text NOT NULL CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            version integer NOT NULL CHECK (version>0),
            action text NOT NULL CHECK (action IN ('created','updated','invalidated')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,id,version),
            FOREIGN KEY (account_id,id) REFERENCES nightingale.declared_medications(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("ALTER TABLE nightingale.declared_medications ADD CONSTRAINT declared_medication_current_version FOREIGN KEY (account_id,id,version) REFERENCES nightingale.declared_medication_histories(account_id,id,version) DEFERRABLE INITIALLY DEFERRED")
    op.execute("CREATE INDEX ix_declared_medications_list ON nightingale.declared_medications(account_id,patient_id,record_status,id)")
    op.execute("CREATE INDEX ix_declared_medications_review ON nightingale.declared_medications(account_id,patient_id,review_status,id)")
    op.execute("CREATE INDEX ix_declared_medications_encounter ON nightingale.declared_medications(account_id,encounter_id,patient_id)")
    op.execute("CREATE INDEX ix_declared_medication_history_receipt ON nightingale.declared_medication_histories(account_id,actor_user_id,operation_id)")
    op.execute("""
        CREATE FUNCTION nightingale.check_declared_medication() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer;
        BEGIN
            SELECT version INTO current_version FROM nightingale.declared_medications WHERE account_id=NEW.account_id AND id=NEW.id;
            SELECT count(*),max(version) INTO entries,current_version FROM nightingale.declared_medication_histories WHERE account_id=NEW.account_id AND id=NEW.id;
            IF current_version IS NULL OR entries<>current_version OR (SELECT count(*) FROM nightingale.declared_medications i JOIN nightingale.declared_medication_histories h ON h.account_id=i.account_id AND h.id=i.id AND h.version=i.version WHERE i.account_id=NEW.account_id AND i.id=NEW.id AND ROW(h.patient_id,h.encounter_id,h.medication_name,h.source_type,h.start_date,h.end_date,h.dose_description,h.frequency_description,h.prescriber_name,h.route_description,h.review_status,h.reviewed_at,h.reviewed_by_user_id,h.captured_at_local,h.record_status,h.correction_reason) IS NOT DISTINCT FROM ROW(i.patient_id,i.encounter_id,i.medication_name,i.source_type,i.start_date,i.end_date,i.dose_description,i.frequency_description,i.prescriber_name,i.route_description,i.review_status,i.reviewed_at,i.reviewed_by_user_id,i.captured_at_local,i.record_status,i.correction_reason))<>1 THEN
                RAISE EXCEPTION 'Declared medication and history disagree' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE CONSTRAINT TRIGGER check_declared_medication_current AFTER INSERT OR UPDATE ON nightingale.declared_medications DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_declared_medication()")
    op.execute("CREATE CONSTRAINT TRIGGER check_declared_medication_history AFTER INSERT ON nightingale.declared_medication_histories DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_declared_medication()")
    op.execute("CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.declared_medication_histories FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
    op.execute("CREATE TRIGGER guard_clinical_identity BEFORE UPDATE ON nightingale.declared_medications FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_identity()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_declared_medication() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.declared_medications TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.declared_medication_histories TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.declared_medications CASCADE")
    op.execute("DROP TABLE nightingale.declared_medication_histories")
    op.execute("DROP FUNCTION nightingale.check_declared_medication()")
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_clinical_sections(value jsonb) RETURNS boolean
        LANGUAGE sql IMMUTABLE AS $$
            SELECT jsonb_typeof(value)='array'
                AND value <@ '["profile","conditions","allergies","encounters","notes","measurements","immunizations","antecedents"]'::jsonb
                AND (SELECT count(*)=count(DISTINCT item)
                    FROM jsonb_array_elements_text(value) AS section(item));
        $$
    """)
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute("""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN (
            'members','owner','clinical_profile','clinical_conditions','clinical_allergies',
            'clinical_encounters','clinical_notes','clinical_measurements',
            'clinical_immunizations','clinical_antecedents'
        ))
    """)
    op.execute("ALTER TABLE nightingale.operation_receipts DROP CONSTRAINT operation_receipts_clinical_section_check")
    op.execute("""
        ALTER TABLE nightingale.operation_receipts
        ADD CONSTRAINT operation_receipts_clinical_section_check
        CHECK (clinical_section IN (
            'profile','conditions','allergies','encounters','notes',
            'measurements','immunizations','antecedents'
        ))
    """)
    op.execute("ALTER TABLE nightingale.account_memberships DROP COLUMN declared_medications_access")
