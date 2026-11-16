"""Clinical encounters, immutable versions and timeline projection."""

from alembic import op

revision = "20261116_05"
down_revision = "20261116_04"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE nightingale.appointments ADD CONSTRAINT appointments_account_id_id_patient_id_key UNIQUE (account_id,id,patient_id)")
    op.execute("""
        CREATE TABLE nightingale.clinical_encounters (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            appointment_id uuid,
            attending_professional_id uuid NOT NULL,
            assistant_user_id uuid,
            occurred_at timestamptz NOT NULL CHECK (isfinite(occurred_at)),
            ended_at timestamptz CHECK (isfinite(ended_at) AND ended_at>=occurred_at),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            reason text CHECK (reason IS NULL OR btrim(reason)<>''),
            reason_source_type text NOT NULL DEFAULT 'unknown' CHECK (reason_source_type IN ('patient','related_person','professional','external_document','unknown')),
            history_present_illness text CHECK (history_present_illness IS NULL OR btrim(history_present_illness)<>''),
            findings text CHECK (findings IS NULL OR btrim(findings)<>''),
            assessment text CHECK (assessment IS NULL OR btrim(assessment)<>''),
            indications text CHECK (indications IS NULL OR btrim(indications)<>''),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            created_by_user_id uuid NOT NULL,
            updated_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,appointment_id,patient_id) REFERENCES nightingale.appointments(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,attending_professional_id) REFERENCES nightingale.account_professionals(account_id,professional_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,assistant_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.clinical_encounter_histories (
            account_id uuid NOT NULL,
            id uuid NOT NULL,
            patient_id uuid NOT NULL,
            appointment_id uuid,
            attending_professional_id uuid NOT NULL,
            assistant_user_id uuid,
            occurred_at timestamptz NOT NULL CHECK (isfinite(occurred_at)),
            ended_at timestamptz CHECK (isfinite(ended_at) AND ended_at>=occurred_at),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            reason text CHECK (reason IS NULL OR btrim(reason)<>''),
            reason_source_type text NOT NULL CHECK (reason_source_type IN ('patient','related_person','professional','external_document','unknown')),
            history_present_illness text CHECK (history_present_illness IS NULL OR btrim(history_present_illness)<>''),
            findings text CHECK (findings IS NULL OR btrim(findings)<>''),
            assessment text CHECK (assessment IS NULL OR btrim(assessment)<>''),
            indications text CHECK (indications IS NULL OR btrim(indications)<>''),
            record_status text NOT NULL CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            version integer NOT NULL CHECK (version>0),
            action text NOT NULL CHECK (action IN ('created','updated','invalidated')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,id,version),
            FOREIGN KEY (account_id,id) REFERENCES nightingale.clinical_encounters(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("ALTER TABLE nightingale.clinical_encounters ADD CONSTRAINT clinical_encounter_current_version FOREIGN KEY (account_id,id,version) REFERENCES nightingale.clinical_encounter_histories(account_id,id,version) DEFERRABLE INITIALLY DEFERRED")
    op.execute("""
        CREATE TABLE nightingale.patient_clinical_timeline (
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            entry_type text NOT NULL CHECK (entry_type IN ('encounter','note','measurement','immunization','antecedent','condition','allergy_intolerance')),
            entry_id uuid NOT NULL CHECK (uuid_extract_version(entry_id) IS NOT DISTINCT FROM 7),
            source_section text NOT NULL CHECK (source_section IN ('encounters','notes','measurements','immunizations','antecedents','conditions','allergies')),
            occurred_at timestamptz CHECK (isfinite(occurred_at)),
            occurrence_date text CHECK (occurrence_date IS NULL OR occurrence_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            date_precision text NOT NULL CHECK (date_precision IN ('instant','year','month','day','reference')),
            sort_key text NOT NULL CHECK (btrim(sort_key)<>''),
            accepted_at timestamptz NOT NULL CHECK (isfinite(accepted_at)),
            entity_version integer NOT NULL CHECK (entity_version>0),
            record_status text NOT NULL CHECK (record_status IN ('valid','entered-in-error')),
            PRIMARY KEY (account_id,patient_id,entry_type,entry_id),
            CHECK ((occurred_at IS NULL)<>(occurrence_date IS NULL)),
            CHECK ((entry_type='encounter' AND source_section='encounters') OR (entry_type='note' AND source_section='notes') OR (entry_type='measurement' AND source_section='measurements') OR (entry_type='immunization' AND source_section='immunizations') OR (entry_type='antecedent' AND source_section='antecedents') OR (entry_type='condition' AND source_section='conditions') OR (entry_type='allergy_intolerance' AND source_section='allergies')),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT
        )
    """)
    op.execute("CREATE INDEX ix_clinical_encounters_last_visit ON nightingale.clinical_encounters(account_id,patient_id,record_status,occurred_at,id)")
    op.execute("CREATE INDEX ix_clinical_encounters_appointment ON nightingale.clinical_encounters(account_id,appointment_id,patient_id)")
    op.execute("CREATE INDEX ix_clinical_encounter_history_receipt ON nightingale.clinical_encounter_histories(account_id,actor_user_id,operation_id)")
    op.execute("CREATE INDEX ix_clinical_timeline_history ON nightingale.patient_clinical_timeline(account_id,patient_id,record_status,sort_key,entry_type,entry_id)")
    op.execute("CREATE INDEX ix_clinical_timeline_section ON nightingale.patient_clinical_timeline(account_id,patient_id,source_section,record_status,sort_key,entry_type,entry_id)")
    op.execute("""
        CREATE FUNCTION nightingale.check_clinical_encounter() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer;
        BEGIN
            SELECT version INTO current_version FROM nightingale.clinical_encounters
                WHERE account_id=NEW.account_id AND id=NEW.id;
            SELECT count(*),max(version) INTO entries,current_version FROM nightingale.clinical_encounter_histories
                WHERE account_id=NEW.account_id AND id=NEW.id;
            IF current_version IS NULL OR entries<>current_version
                OR (SELECT count(*) FROM nightingale.clinical_encounters e
                    JOIN nightingale.clinical_encounter_histories h ON h.account_id=e.account_id AND h.id=e.id AND h.version=e.version
                    WHERE e.account_id=NEW.account_id AND e.id=NEW.id
                    AND ROW(h.patient_id,h.appointment_id,h.attending_professional_id,h.assistant_user_id,h.occurred_at,h.ended_at,h.captured_at_local,h.reason,h.reason_source_type,h.history_present_illness,h.findings,h.assessment,h.indications,h.record_status,h.correction_reason)
                        IS NOT DISTINCT FROM ROW(e.patient_id,e.appointment_id,e.attending_professional_id,e.assistant_user_id,e.occurred_at,e.ended_at,e.captured_at_local,e.reason,e.reason_source_type,e.history_present_illness,e.findings,e.assessment,e.indications,e.record_status,e.correction_reason))<>1 THEN
                RAISE EXCEPTION 'Clinical encounter and history disagree' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE CONSTRAINT TRIGGER check_clinical_encounter_current AFTER INSERT OR UPDATE ON nightingale.clinical_encounters DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_clinical_encounter()")
    op.execute("CREATE CONSTRAINT TRIGGER check_clinical_encounter_history AFTER INSERT ON nightingale.clinical_encounter_histories DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_clinical_encounter()")
    op.execute("CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.clinical_encounter_histories FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
    op.execute("CREATE TRIGGER guard_clinical_identity BEFORE UPDATE ON nightingale.clinical_encounters FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_identity()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_clinical_encounter() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.clinical_encounters TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.clinical_encounter_histories TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON nightingale.patient_clinical_timeline TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.patient_clinical_timeline")
    op.execute("DROP TABLE nightingale.clinical_encounters CASCADE")
    op.execute("DROP TABLE nightingale.clinical_encounter_histories")
    op.execute("DROP FUNCTION nightingale.check_clinical_encounter()")
    op.execute("ALTER TABLE nightingale.appointments DROP CONSTRAINT appointments_account_id_id_patient_id_key")
