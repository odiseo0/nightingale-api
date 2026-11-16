"""Patient measurements with typed values and immutable history."""

from alembic import op

revision = "20261116_07"
down_revision = "20261116_06"
branch_labels = None
depends_on = None

SHAPE = """
    kind IN ('weight','temperature','oxygen_saturation','heart_rate','blood_pressure')
    AND ((kind='blood_pressure' AND value IS NULL AND unit='mm[Hg]'
        AND (systolic_value IS NOT NULL OR diastolic_value IS NOT NULL)
        AND (systolic_value IS NULL OR systolic_value BETWEEN 20 AND 300)
        AND (diastolic_value IS NULL OR diastolic_value BETWEEN 20 AND 300))
    OR (kind<>'blood_pressure' AND value IS NOT NULL AND systolic_value IS NULL AND diastolic_value IS NULL
        AND ((kind='weight' AND unit='kg' AND value BETWEEN 0.01 AND 1000)
        OR (kind='temperature' AND unit='Cel' AND value BETWEEN 20 AND 45)
        OR (kind='oxygen_saturation' AND unit='%' AND value BETWEEN 0 AND 100)
        OR (kind='heart_rate' AND unit='/min' AND value BETWEEN 1 AND 300))))
"""


def upgrade():
    op.execute(f"""
        CREATE TABLE nightingale.patient_measurements (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            kind text NOT NULL,
            measured_at timestamptz NOT NULL CHECK (isfinite(measured_at)),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            method text CHECK (method IS NULL OR btrim(method)<>''),
            body_site text CHECK (body_site IS NULL OR btrim(body_site)<>''),
            value numeric,
            systolic_value numeric,
            diastolic_value numeric,
            unit text NOT NULL,
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            created_by_user_id uuid NOT NULL,
            updated_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            CHECK ({SHAPE}),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id) REFERENCES nightingale.clinical_encounters(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute(f"""
        CREATE TABLE nightingale.patient_measurement_histories (
            account_id uuid NOT NULL,
            id uuid NOT NULL,
            patient_id uuid NOT NULL,
            encounter_id uuid,
            kind text NOT NULL,
            measured_at timestamptz NOT NULL CHECK (isfinite(measured_at)),
            captured_at_local timestamptz CHECK (isfinite(captured_at_local)),
            method text CHECK (method IS NULL OR btrim(method)<>''),
            body_site text CHECK (body_site IS NULL OR btrim(body_site)<>''),
            value numeric,
            systolic_value numeric,
            diastolic_value numeric,
            unit text NOT NULL,
            record_status text NOT NULL CHECK (record_status IN ('valid','entered-in-error')),
            correction_reason text CHECK (correction_reason IS NULL OR btrim(correction_reason)<>''),
            version integer NOT NULL CHECK (version>0),
            action text NOT NULL CHECK (action IN ('created','updated','invalidated')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,id,version),
            CHECK ({SHAPE}),
            FOREIGN KEY (account_id,id) REFERENCES nightingale.patient_measurements(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("ALTER TABLE nightingale.patient_measurements ADD CONSTRAINT patient_measurement_current_version FOREIGN KEY (account_id,id,version) REFERENCES nightingale.patient_measurement_histories(account_id,id,version) DEFERRABLE INITIALLY DEFERRED")
    op.execute("CREATE INDEX ix_patient_measurements_series ON nightingale.patient_measurements(account_id,patient_id,kind,record_status,measured_at,id)")
    op.execute("CREATE INDEX ix_patient_measurements_encounter ON nightingale.patient_measurements(account_id,encounter_id,patient_id)")
    op.execute("CREATE INDEX ix_patient_measurement_history_receipt ON nightingale.patient_measurement_histories(account_id,actor_user_id,operation_id)")
    op.execute("""
        CREATE FUNCTION nightingale.check_patient_measurement() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer;
        BEGIN
            SELECT version INTO current_version FROM nightingale.patient_measurements WHERE account_id=NEW.account_id AND id=NEW.id;
            SELECT count(*),max(version) INTO entries,current_version FROM nightingale.patient_measurement_histories WHERE account_id=NEW.account_id AND id=NEW.id;
            IF current_version IS NULL OR entries<>current_version OR (SELECT count(*) FROM nightingale.patient_measurements m JOIN nightingale.patient_measurement_histories h ON h.account_id=m.account_id AND h.id=m.id AND h.version=m.version WHERE m.account_id=NEW.account_id AND m.id=NEW.id AND ROW(h.patient_id,h.encounter_id,h.kind,h.measured_at,h.captured_at_local,h.method,h.body_site,h.value,h.systolic_value,h.diastolic_value,h.unit,h.record_status,h.correction_reason) IS NOT DISTINCT FROM ROW(m.patient_id,m.encounter_id,m.kind,m.measured_at,m.captured_at_local,m.method,m.body_site,m.value,m.systolic_value,m.diastolic_value,m.unit,m.record_status,m.correction_reason))<>1 THEN
                RAISE EXCEPTION 'Patient measurement and history disagree' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE CONSTRAINT TRIGGER check_patient_measurement_current AFTER INSERT OR UPDATE ON nightingale.patient_measurements DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_measurement()")
    op.execute("CREATE CONSTRAINT TRIGGER check_patient_measurement_history AFTER INSERT ON nightingale.patient_measurement_histories DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_measurement()")
    op.execute("CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.patient_measurement_histories FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
    op.execute("CREATE TRIGGER guard_clinical_identity BEFORE UPDATE ON nightingale.patient_measurements FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_identity()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_patient_measurement() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.patient_measurements TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.patient_measurement_histories TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.patient_measurements CASCADE")
    op.execute("DROP TABLE nightingale.patient_measurement_histories")
    op.execute("DROP FUNCTION nightingale.check_patient_measurement()")
