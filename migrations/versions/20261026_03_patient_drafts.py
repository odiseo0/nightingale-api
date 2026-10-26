"""Stable patient identities, account drafts and declared documents."""

from alembic import op

revision = "20261026_03"
down_revision = "20261026_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.patients (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at)
        )
    """)
    op.execute(r"""
        CREATE TABLE nightingale.account_patients (
            account_id uuid NOT NULL REFERENCES nightingale.accounts(id) ON DELETE RESTRICT,
            patient_id uuid NOT NULL REFERENCES nightingale.patients(id) ON DELETE RESTRICT,
            full_name text CHECK (full_name IS NULL OR length(btrim(full_name))>0),
            birth_date date CHECK (birth_date IS NULL OR isfinite(birth_date)),
            phone_code text,
            phone text,
            identification_basis text CHECK (identification_basis IN ('own_document','minor_without_document')),
            completion_status text NOT NULL DEFAULT 'draft' CHECK (completion_status IN ('draft','complete')),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            PRIMARY KEY (account_id,patient_id),
            CHECK ((phone_code IS NULL AND phone IS NULL) OR
                (phone_code IS NOT NULL AND phone IS NOT NULL AND phone_code ~ '^\+[1-9][0-9]{0,2}$' AND phone ~ '^[0-9]+$')),
            CHECK (completion_status='draft' OR (full_name IS NOT NULL AND identification_basis IS NOT NULL
                AND (identification_basis<>'minor_without_document' OR birth_date IS NOT NULL)))
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.patient_identifiers (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            patient_id uuid NOT NULL REFERENCES nightingale.patients(id) ON DELETE RESTRICT,
            issuing_country text NOT NULL DEFAULT 'VE' CHECK (issuing_country ~ '^[A-Z]{2}$'),
            document_type text COLLATE "C" NOT NULL CHECK (document_type IN ('national_id','passport')),
            document_number text COLLATE "C" NOT NULL CHECK (length(btrim(document_number))>0),
            verification_status text NOT NULL DEFAULT 'declared' CHECK (verification_status IN ('declared','verified','invalidated')),
            verified_at timestamptz,
            verified_by_user_id uuid REFERENCES nightingale.app_users(id) ON DELETE RESTRICT,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            CHECK ((verified_at IS NULL)=(verified_by_user_id IS NULL)),
            CHECK (verified_at IS NULL OR (isfinite(verified_at) AND verified_at>=created_at AND verified_at<=updated_at)),
            CHECK ((verification_status='declared' AND verified_at IS NULL) OR
                (verification_status='verified' AND verified_at IS NOT NULL) OR verification_status='invalidated')
        )
    """)
    op.execute("CREATE INDEX ix_account_patients_patient ON nightingale.account_patients(patient_id,account_id)")
    op.execute("CREATE INDEX ix_account_patients_state ON nightingale.account_patients(account_id,completion_status,status)")
    op.execute("CREATE UNIQUE INDEX uq_patient_identifiers_verified ON nightingale.patient_identifiers(issuing_country,document_type,document_number) WHERE verification_status='verified'")
    op.execute("CREATE INDEX ix_patient_identifiers_patient ON nightingale.patient_identifiers(patient_id,verification_status)")
    op.execute("CREATE INDEX ix_patient_identifiers_verifier ON nightingale.patient_identifiers(verified_by_user_id)")
    op.execute("""
        CREATE FUNCTION nightingale.guard_patient_record() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.created_at IS DISTINCT FROM OLD.created_at OR NEW.updated_at<OLD.updated_at THEN
                RAISE EXCEPTION 'Patient record times are immutable or monotonic' USING ERRCODE='23514';
            END IF;
            IF TG_TABLE_NAME='patients' THEN
                IF NEW.id IS DISTINCT FROM OLD.id THEN
                    RAISE EXCEPTION 'Patient identity is immutable' USING ERRCODE='23514';
                END IF;
            ELSE
                IF NEW.patient_id IS DISTINCT FROM OLD.patient_id OR NEW.version<>OLD.version+1 THEN
                    RAISE EXCEPTION 'Patient reference or version is invalid' USING ERRCODE='23514';
                END IF;
                IF TG_TABLE_NAME='account_patients' THEN
                    IF NEW.account_id IS DISTINCT FROM OLD.account_id THEN
                        RAISE EXCEPTION 'Profile account is immutable' USING ERRCODE='23514';
                    END IF;
                ELSE
                    IF NEW.id IS DISTINCT FROM OLD.id OR
                        (OLD.verification_status<>'declared' AND
                            (NEW.issuing_country,NEW.document_type,NEW.document_number) IS DISTINCT FROM
                            (OLD.issuing_country,OLD.document_type,OLD.document_number)) OR
                        (OLD.verified_at IS NOT NULL AND (NEW.verified_at,NEW.verified_by_user_id)
                            IS DISTINCT FROM (OLD.verified_at,OLD.verified_by_user_id)) OR
                        (OLD.verified_at IS NULL AND NEW.verified_at IS NOT NULL AND
                            NOT (OLD.verification_status='declared' AND NEW.verification_status='verified')) OR
                        (OLD.verification_status='verified' AND NEW.verification_status NOT IN ('verified','invalidated')) OR
                        (OLD.verification_status='invalidated' AND NEW.verification_status<>'invalidated') THEN
                        RAISE EXCEPTION 'Document identity or evidence is immutable' USING ERRCODE='23514';
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END; $$
    """)
    for table in ("patients", "account_patients", "patient_identifiers"):
        op.execute(f"CREATE TRIGGER guard_patient_record BEFORE UPDATE ON nightingale.{table} FOR EACH ROW EXECUTE FUNCTION nightingale.guard_patient_record()")
        op.execute(f"GRANT SELECT,INSERT,UPDATE ON nightingale.{table} TO nightingale_runtime")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_patient_record() FROM PUBLIC")


def downgrade():
    for table in ("patient_identifiers", "account_patients", "patients"):
        op.execute(f"DROP TABLE nightingale.{table}")
    op.execute("DROP FUNCTION nightingale.guard_patient_record()")
