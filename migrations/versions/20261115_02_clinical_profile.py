"""Patient clinical profile, immutable history and birth-date changes."""

from alembic import op

revision = "20261115_02"
down_revision = "20261115_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.patient_clinical_profiles (
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            sex_at_birth text CHECK (sex_at_birth IN ('male','female','other','unknown')),
            source_type text NOT NULL DEFAULT 'unknown' CHECK (source_type IN ('patient','related_person','professional','external_document','unknown')),
            created_by_user_id uuid NOT NULL,
            updated_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            PRIMARY KEY (account_id,patient_id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.patient_clinical_profile_histories (
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            version integer NOT NULL CHECK (version>0),
            sex_at_birth text CHECK (sex_at_birth IN ('male','female','other','unknown')),
            source_type text NOT NULL CHECK (source_type IN ('patient','related_person','professional','external_document','unknown')),
            action text NOT NULL CHECK (action='set'),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,patient_id,version),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.patient_clinical_profiles(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("CREATE INDEX ix_clinical_profile_history_receipt ON nightingale.patient_clinical_profile_histories(account_id,actor_user_id,operation_id)")
    op.execute("""
        ALTER TABLE nightingale.patient_clinical_profiles
        ADD CONSTRAINT clinical_profile_current_version
        FOREIGN KEY (account_id,patient_id,version)
        REFERENCES nightingale.patient_clinical_profile_histories(account_id,patient_id,version)
        DEFERRABLE INITIALLY DEFERRED
    """)
    op.execute("""
        CREATE TABLE nightingale.patient_birth_date_changes (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            previous_birth_date date,
            new_birth_date date,
            patient_version integer NOT NULL CHECK (patient_version>0),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            CHECK (previous_birth_date IS DISTINCT FROM new_birth_date),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("CREATE INDEX ix_birth_changes_patient ON nightingale.patient_birth_date_changes(account_id,patient_id,id)")
    op.execute("CREATE INDEX ix_birth_changes_receipt ON nightingale.patient_birth_date_changes(account_id,actor_user_id,operation_id)")
    op.execute("""
        CREATE FUNCTION nightingale.check_clinical_profile() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer;
        BEGIN
            SELECT version INTO current_version FROM nightingale.patient_clinical_profiles
                WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id;
            SELECT count(*),max(version) INTO entries,current_version FROM nightingale.patient_clinical_profile_histories
                WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id;
            IF current_version IS NULL OR entries<>current_version
                OR (SELECT count(*) FROM nightingale.patient_clinical_profiles p
                    JOIN nightingale.patient_clinical_profile_histories h USING(account_id,patient_id,version)
                    WHERE p.account_id=NEW.account_id AND p.patient_id=NEW.patient_id
                    AND p.sex_at_birth IS NOT DISTINCT FROM h.sex_at_birth AND p.source_type=h.source_type)<>1 THEN
                RAISE EXCEPTION 'Clinical profile and history disagree' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER check_clinical_profile_current AFTER INSERT OR UPDATE ON nightingale.patient_clinical_profiles
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_clinical_profile()
    """)
    op.execute("""
        CREATE CONSTRAINT TRIGGER check_clinical_profile_history AFTER INSERT ON nightingale.patient_clinical_profile_histories
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_clinical_profile()
    """)
    op.execute("""
        CREATE FUNCTION nightingale.guard_clinical_history() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Clinical history is append-only' USING ERRCODE='42501';
        END; $$
    """)
    for table in ("patient_clinical_profile_histories", "patient_birth_date_changes"):
        op.execute(f"CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.{table} FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_clinical_profile() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_clinical_history() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.patient_clinical_profiles TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.patient_clinical_profile_histories TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.patient_birth_date_changes TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.patient_birth_date_changes")
    op.execute("DROP TABLE nightingale.patient_clinical_profiles CASCADE")
    op.execute("DROP TABLE nightingale.patient_clinical_profile_histories")
    op.execute("DROP FUNCTION nightingale.check_clinical_profile()")
    op.execute("DROP FUNCTION nightingale.guard_clinical_history()")
