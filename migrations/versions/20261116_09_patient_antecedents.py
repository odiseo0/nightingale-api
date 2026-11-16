"""Narrative patient antecedents with immutable history."""

from alembic import op

revision = "20261116_09"
down_revision = "20261116_08"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.patient_antecedents (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            category text NOT NULL CHECK (category IN ('personal','family','other')),
            content text NOT NULL CHECK (btrim(content)<>''),
            related_person_description text CHECK (related_person_description IS NULL OR btrim(related_person_description)<>''),
            occurrence_date text CHECK (occurrence_date IS NULL OR occurrence_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            source_type text NOT NULL DEFAULT 'unknown' CHECK (source_type IN ('patient','related_person','professional','external_document','unknown')),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            created_by_user_id uuid NOT NULL,
            updated_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            CHECK (category<>'family' OR related_person_description IS NOT NULL),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id) REFERENCES nightingale.clinical_encounters(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.patient_antecedent_histories (
            account_id uuid NOT NULL,
            id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            category text NOT NULL CHECK (category IN ('personal','family','other')),
            content text NOT NULL CHECK (btrim(content)<>''),
            related_person_description text CHECK (related_person_description IS NULL OR btrim(related_person_description)<>''),
            occurrence_date text CHECK (occurrence_date IS NULL OR occurrence_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            source_type text NOT NULL CHECK (source_type IN ('patient','related_person','professional','external_document','unknown')),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            record_status text NOT NULL CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            version integer NOT NULL CHECK (version>0),
            action text NOT NULL CHECK (action IN ('created','updated','invalidated')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,id,version),
            CHECK (category<>'family' OR related_person_description IS NOT NULL),
            FOREIGN KEY (account_id,id) REFERENCES nightingale.patient_antecedents(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("ALTER TABLE nightingale.patient_antecedents ADD CONSTRAINT patient_antecedent_current_version FOREIGN KEY (account_id,id,version) REFERENCES nightingale.patient_antecedent_histories(account_id,id,version) DEFERRABLE INITIALLY DEFERRED")
    op.execute("CREATE INDEX ix_patient_antecedents_list ON nightingale.patient_antecedents(account_id,patient_id,category,record_status,id)")
    op.execute("CREATE INDEX ix_patient_antecedents_encounter ON nightingale.patient_antecedents(account_id,encounter_id,patient_id)")
    op.execute("CREATE INDEX ix_patient_antecedent_history_receipt ON nightingale.patient_antecedent_histories(account_id,actor_user_id,operation_id)")
    op.execute("""
        CREATE FUNCTION nightingale.check_patient_antecedent() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer;
        BEGIN
            SELECT version INTO current_version FROM nightingale.patient_antecedents WHERE account_id=NEW.account_id AND id=NEW.id;
            SELECT count(*),max(version) INTO entries,current_version FROM nightingale.patient_antecedent_histories WHERE account_id=NEW.account_id AND id=NEW.id;
            IF current_version IS NULL OR entries<>current_version OR (SELECT count(*) FROM nightingale.patient_antecedents a JOIN nightingale.patient_antecedent_histories h ON h.account_id=a.account_id AND h.id=a.id AND h.version=a.version WHERE a.account_id=NEW.account_id AND a.id=NEW.id AND ROW(h.patient_id,h.encounter_id,h.category,h.content,h.related_person_description,h.occurrence_date,h.source_type,h.captured_at_local,h.record_status,h.correction_reason) IS NOT DISTINCT FROM ROW(a.patient_id,a.encounter_id,a.category,a.content,a.related_person_description,a.occurrence_date,a.source_type,a.captured_at_local,a.record_status,a.correction_reason))<>1 THEN
                RAISE EXCEPTION 'Patient antecedent and history disagree' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE CONSTRAINT TRIGGER check_patient_antecedent_current AFTER INSERT OR UPDATE ON nightingale.patient_antecedents DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_antecedent()")
    op.execute("CREATE CONSTRAINT TRIGGER check_patient_antecedent_history AFTER INSERT ON nightingale.patient_antecedent_histories DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_antecedent()")
    op.execute("CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.patient_antecedent_histories FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
    op.execute("CREATE TRIGGER guard_clinical_identity BEFORE UPDATE ON nightingale.patient_antecedents FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_identity()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_patient_antecedent() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.patient_antecedents TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.patient_antecedent_histories TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.patient_antecedents CASCADE")
    op.execute("DROP TABLE nightingale.patient_antecedent_histories")
    op.execute("DROP FUNCTION nightingale.check_patient_antecedent()")
