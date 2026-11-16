"""Patient notes with immutable version history."""

from alembic import op

revision = "20261116_06"
down_revision = "20261116_05"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.patient_notes (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            body text NOT NULL CHECK (btrim(body)<>''),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            created_by_user_id uuid NOT NULL,
            updated_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id) REFERENCES nightingale.clinical_encounters(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.patient_note_histories (
            account_id uuid NOT NULL,
            id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            body text NOT NULL CHECK (btrim(body)<>''),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            record_status text NOT NULL CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            version integer NOT NULL CHECK (version>0),
            action text NOT NULL CHECK (action IN ('created','updated','invalidated')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,id,version),
            FOREIGN KEY (account_id,id) REFERENCES nightingale.patient_notes(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("ALTER TABLE nightingale.patient_notes ADD CONSTRAINT patient_note_current_version FOREIGN KEY (account_id,id,version) REFERENCES nightingale.patient_note_histories(account_id,id,version) DEFERRABLE INITIALLY DEFERRED")
    op.execute("CREATE INDEX ix_patient_notes_list ON nightingale.patient_notes(account_id,patient_id,record_status,id)")
    op.execute("CREATE INDEX ix_patient_notes_encounter ON nightingale.patient_notes(account_id,encounter_id,patient_id)")
    op.execute("CREATE INDEX ix_patient_note_history_receipt ON nightingale.patient_note_histories(account_id,actor_user_id,operation_id)")
    op.execute("""
        CREATE FUNCTION nightingale.check_patient_note() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer;
        BEGIN
            SELECT version INTO current_version FROM nightingale.patient_notes WHERE account_id=NEW.account_id AND id=NEW.id;
            SELECT count(*),max(version) INTO entries,current_version FROM nightingale.patient_note_histories WHERE account_id=NEW.account_id AND id=NEW.id;
            IF current_version IS NULL OR entries<>current_version OR (SELECT count(*) FROM nightingale.patient_notes n JOIN nightingale.patient_note_histories h ON h.account_id=n.account_id AND h.id=n.id AND h.version=n.version WHERE n.account_id=NEW.account_id AND n.id=NEW.id AND ROW(h.patient_id,h.encounter_id,h.body,h.captured_at_local,h.record_status,h.correction_reason) IS NOT DISTINCT FROM ROW(n.patient_id,n.encounter_id,n.body,n.captured_at_local,n.record_status,n.correction_reason))<>1 THEN
                RAISE EXCEPTION 'Patient note and history disagree' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE CONSTRAINT TRIGGER check_patient_note_current AFTER INSERT OR UPDATE ON nightingale.patient_notes DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_note()")
    op.execute("CREATE CONSTRAINT TRIGGER check_patient_note_history AFTER INSERT ON nightingale.patient_note_histories DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_note()")
    op.execute("CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.patient_note_histories FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
    op.execute("CREATE TRIGGER guard_clinical_identity BEFORE UPDATE ON nightingale.patient_notes FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_identity()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_patient_note() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.patient_notes TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.patient_note_histories TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.patient_notes CASCADE")
    op.execute("DROP TABLE nightingale.patient_note_histories")
    op.execute("DROP FUNCTION nightingale.check_patient_note()")
