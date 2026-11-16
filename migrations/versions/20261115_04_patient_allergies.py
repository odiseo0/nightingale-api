"""Patient allergies and intolerances with immutable history."""

from alembic import op

revision = "20261115_04"
down_revision = "20261115_03"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.patient_allergy_intolerances (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            substance text NOT NULL CHECK (btrim(substance)<>''),
            type text NOT NULL DEFAULT 'unknown' CHECK (type IN ('allergy','intolerance','unknown')),
            reaction_description text,
            clinical_status text NOT NULL DEFAULT 'active' CHECK (clinical_status IN ('active','inactive','resolved')),
            verification_status text NOT NULL DEFAULT 'unconfirmed' CHECK (verification_status IN ('unconfirmed','presumed','confirmed','refuted','entered-in-error')),
            onset_date text CHECK (onset_date IS NULL OR onset_date ~ '^[0-9]{4}(-[0-9]{2}){0,2}$'),
            last_occurrence_date text CHECK (last_occurrence_date IS NULL OR last_occurrence_date ~ '^[0-9]{4}(-[0-9]{2}){0,2}$'),
            source_type text NOT NULL DEFAULT 'unknown' CHECK (source_type IN ('patient','related_person','professional','external_document','unknown')),
            correction_reason text,
            created_by_user_id uuid NOT NULL,
            updated_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute("CREATE INDEX ix_allergies_patient ON nightingale.patient_allergy_intolerances(account_id,patient_id,id)")
    op.execute("CREATE INDEX ix_allergies_created_by ON nightingale.patient_allergy_intolerances(account_id,created_by_user_id)")
    op.execute("CREATE INDEX ix_allergies_updated_by ON nightingale.patient_allergy_intolerances(account_id,updated_by_user_id)")
    op.execute("""
        CREATE TABLE nightingale.patient_allergy_intolerance_histories (
            account_id uuid NOT NULL,
            id uuid NOT NULL,
            patient_id uuid NOT NULL,
            version integer NOT NULL CHECK (version>0),
            substance text NOT NULL CHECK (btrim(substance)<>''),
            type text NOT NULL,
            reaction_description text,
            clinical_status text NOT NULL,
            verification_status text NOT NULL,
            onset_date text,
            last_occurrence_date text,
            source_type text NOT NULL,
            correction_reason text,
            action text NOT NULL CHECK (action IN ('created','updated','invalidated')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,id,version),
            FOREIGN KEY (account_id,id) REFERENCES nightingale.patient_allergy_intolerances(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("CREATE INDEX ix_allergy_history_receipt ON nightingale.patient_allergy_intolerance_histories(account_id,actor_user_id,operation_id)")
    op.execute("""
        ALTER TABLE nightingale.patient_allergy_intolerances ADD CONSTRAINT allergy_current_version
        FOREIGN KEY (account_id,id,version) REFERENCES nightingale.patient_allergy_intolerance_histories(account_id,id,version)
        DEFERRABLE INITIALLY DEFERRED
    """)
    op.execute("""
        CREATE FUNCTION nightingale.check_patient_allergy() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer;
        BEGIN
            SELECT count(*) INTO entries FROM nightingale.patient_allergy_intolerance_histories WHERE account_id=NEW.account_id AND id=NEW.id;
            SELECT version INTO current_version FROM nightingale.patient_allergy_intolerances WHERE account_id=NEW.account_id AND id=NEW.id;
            IF current_version IS NULL OR entries<>current_version OR (SELECT count(*) FROM nightingale.patient_allergy_intolerances a JOIN nightingale.patient_allergy_intolerance_histories h ON h.account_id=a.account_id AND h.id=a.id AND h.version=a.version WHERE a.account_id=NEW.account_id AND a.id=NEW.id AND a.substance=h.substance AND a.type=h.type AND a.reaction_description IS NOT DISTINCT FROM h.reaction_description AND a.clinical_status=h.clinical_status AND a.verification_status=h.verification_status AND a.onset_date IS NOT DISTINCT FROM h.onset_date AND a.last_occurrence_date IS NOT DISTINCT FROM h.last_occurrence_date AND a.source_type=h.source_type AND a.correction_reason IS NOT DISTINCT FROM h.correction_reason)<>1 THEN
                RAISE EXCEPTION 'Allergy and history disagree' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("""
        CREATE FUNCTION nightingale.check_allergy_review() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer; review_status text; pertinent integer;
        BEGIN
            SELECT information_status INTO review_status FROM nightingale.patient_clinical_section_reviews WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id AND section='allergies';
            SELECT count(*) INTO pertinent FROM nightingale.patient_allergy_intolerances WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id AND verification_status NOT IN ('refuted','entered-in-error');
            IF (pertinent>0 AND review_status IS DISTINCT FROM 'has_entries') OR (pertinent=0 AND review_status='has_entries') THEN
                RAISE EXCEPTION 'Allergy section and entries disagree' USING ERRCODE='23514';
            END IF;
            IF review_status IS NOT NULL THEN
                SELECT version INTO current_version FROM nightingale.patient_clinical_section_reviews WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id AND section='allergies';
                SELECT count(*) INTO entries FROM nightingale.patient_clinical_section_review_histories WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id AND section='allergies';
                IF current_version IS NULL OR entries<>current_version OR (SELECT count(*) FROM nightingale.patient_clinical_section_reviews r JOIN nightingale.patient_clinical_section_review_histories h ON h.account_id=r.account_id AND h.patient_id=r.patient_id AND h.section=r.section AND h.version=r.version WHERE r.account_id=NEW.account_id AND r.patient_id=NEW.patient_id AND r.section='allergies' AND r.information_status=h.information_status AND r.source_type=h.source_type)<>1 THEN
                    RAISE EXCEPTION 'Allergy review and history disagree' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NEW;
        END; $$
    """)
    for table in ("patient_allergy_intolerances", "patient_allergy_intolerance_histories"):
        op.execute(f"CREATE CONSTRAINT TRIGGER check_allergy AFTER INSERT OR UPDATE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_allergy()")
        op.execute(f"CREATE CONSTRAINT TRIGGER check_review AFTER INSERT OR UPDATE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_allergy_review()")
    op.execute("CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.patient_allergy_intolerance_histories FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_patient_allergy() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_allergy_review() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.patient_allergy_intolerances TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.patient_allergy_intolerance_histories TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.patient_allergy_intolerances CASCADE")
    op.execute("DROP TABLE nightingale.patient_allergy_intolerance_histories")
    op.execute("DROP FUNCTION nightingale.check_patient_allergy()")
    op.execute("DROP FUNCTION nightingale.check_allergy_review()")
