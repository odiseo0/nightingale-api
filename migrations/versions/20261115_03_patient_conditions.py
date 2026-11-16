"""Patient conditions and coherent clinical section reviews."""

from alembic import op

revision = "20261115_03"
down_revision = "20261115_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.patient_conditions (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            name text NOT NULL CHECK (btrim(name)<>''),
            clinical_status text NOT NULL DEFAULT 'active' CHECK (clinical_status IN ('active','recurrence','relapse','inactive','remission','resolved','unknown')),
            verification_status text NOT NULL DEFAULT 'unconfirmed' CHECK (verification_status IN ('unconfirmed','provisional','differential','confirmed','refuted','entered-in-error')),
            onset_date text CHECK (onset_date IS NULL OR onset_date ~ '^[0-9]{4}(-[0-9]{2}){0,2}$'),
            abatement_date text CHECK (abatement_date IS NULL OR abatement_date ~ '^[0-9]{4}(-[0-9]{2}){0,2}$'),
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
    op.execute("CREATE INDEX ix_conditions_patient ON nightingale.patient_conditions(account_id,patient_id,id)")
    op.execute("CREATE INDEX ix_conditions_created_by ON nightingale.patient_conditions(account_id,created_by_user_id)")
    op.execute("CREATE INDEX ix_conditions_updated_by ON nightingale.patient_conditions(account_id,updated_by_user_id)")
    op.execute("""
        CREATE TABLE nightingale.patient_condition_histories (
            account_id uuid NOT NULL,
            id uuid NOT NULL,
            patient_id uuid NOT NULL,
            version integer NOT NULL CHECK (version>0),
            name text NOT NULL CHECK (btrim(name)<>''),
            clinical_status text NOT NULL,
            verification_status text NOT NULL,
            onset_date text,
            abatement_date text,
            source_type text NOT NULL,
            correction_reason text,
            action text NOT NULL CHECK (action IN ('created','updated','invalidated')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,id,version),
            FOREIGN KEY (account_id,id) REFERENCES nightingale.patient_conditions(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("CREATE INDEX ix_condition_history_receipt ON nightingale.patient_condition_histories(account_id,actor_user_id,operation_id)")
    op.execute("""
        ALTER TABLE nightingale.patient_conditions ADD CONSTRAINT condition_current_version
        FOREIGN KEY (account_id,id,version) REFERENCES nightingale.patient_condition_histories(account_id,id,version)
        DEFERRABLE INITIALLY DEFERRED
    """)
    op.execute("""
        CREATE TABLE nightingale.patient_clinical_section_reviews (
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            section text NOT NULL CHECK (section IN ('conditions','allergies')),
            information_status text NOT NULL CHECK (information_status IN ('not_asked','unknown','none_known','has_entries')),
            source_type text NOT NULL DEFAULT 'unknown' CHECK (source_type IN ('patient','related_person','professional','external_document','unknown')),
            reviewed_by_user_id uuid NOT NULL,
            reviewed_at timestamptz NOT NULL CHECK (isfinite(reviewed_at)),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            PRIMARY KEY (account_id,patient_id,section),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,reviewed_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.patient_clinical_section_review_histories (
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            section text NOT NULL,
            version integer NOT NULL CHECK (version>0),
            information_status text NOT NULL,
            source_type text NOT NULL,
            action text NOT NULL CHECK (action IN ('set','derived')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,patient_id,section,version),
            FOREIGN KEY (account_id,patient_id,section) REFERENCES nightingale.patient_clinical_section_reviews(account_id,patient_id,section) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
        )
    """)
    op.execute("CREATE INDEX ix_section_review_history_receipt ON nightingale.patient_clinical_section_review_histories(account_id,actor_user_id,operation_id)")
    op.execute("""
        ALTER TABLE nightingale.patient_clinical_section_reviews ADD CONSTRAINT section_review_current_version
        FOREIGN KEY (account_id,patient_id,section,version)
        REFERENCES nightingale.patient_clinical_section_review_histories(account_id,patient_id,section,version)
        DEFERRABLE INITIALLY DEFERRED
    """)
    op.execute("""
        CREATE FUNCTION nightingale.check_patient_condition() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer; review_status text;
        BEGIN
            SELECT count(*) INTO entries FROM nightingale.patient_condition_histories WHERE account_id=NEW.account_id AND id=NEW.id;
            SELECT version INTO current_version FROM nightingale.patient_conditions WHERE account_id=NEW.account_id AND id=NEW.id;
            IF current_version IS NULL OR entries<>current_version OR (SELECT count(*) FROM nightingale.patient_conditions c JOIN nightingale.patient_condition_histories h ON h.account_id=c.account_id AND h.id=c.id AND h.version=c.version WHERE c.account_id=NEW.account_id AND c.id=NEW.id AND c.name=h.name AND c.clinical_status=h.clinical_status AND c.verification_status=h.verification_status AND c.onset_date IS NOT DISTINCT FROM h.onset_date AND c.abatement_date IS NOT DISTINCT FROM h.abatement_date AND c.source_type=h.source_type AND c.correction_reason IS NOT DISTINCT FROM h.correction_reason)<>1 THEN
                RAISE EXCEPTION 'Condition and history disagree' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("""
        CREATE FUNCTION nightingale.check_section_review() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE current_version integer; entries integer; review_status text; pertinent integer;
        BEGIN
            SELECT information_status INTO review_status FROM nightingale.patient_clinical_section_reviews WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id AND section='conditions';
            SELECT count(*) INTO pertinent FROM nightingale.patient_conditions WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id AND verification_status NOT IN ('refuted','entered-in-error');
            IF (pertinent>0 AND review_status IS DISTINCT FROM 'has_entries') OR (pertinent=0 AND review_status='has_entries') THEN
                RAISE EXCEPTION 'Clinical section and entries disagree' USING ERRCODE='23514';
            END IF;
            IF review_status IS NOT NULL THEN
                SELECT version INTO current_version FROM nightingale.patient_clinical_section_reviews WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id AND section='conditions';
                SELECT count(*) INTO entries FROM nightingale.patient_clinical_section_review_histories WHERE account_id=NEW.account_id AND patient_id=NEW.patient_id AND section='conditions';
                IF current_version IS NULL OR entries<>current_version OR (SELECT count(*) FROM nightingale.patient_clinical_section_reviews r JOIN nightingale.patient_clinical_section_review_histories h ON h.account_id=r.account_id AND h.patient_id=r.patient_id AND h.section=r.section AND h.version=r.version WHERE r.account_id=NEW.account_id AND r.patient_id=NEW.patient_id AND r.section='conditions' AND r.information_status=h.information_status AND r.source_type=h.source_type)<>1 THEN
                    RAISE EXCEPTION 'Clinical review and history disagree' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NEW;
        END; $$
    """)
    for table in ("patient_conditions", "patient_condition_histories"):
        op.execute(f"CREATE CONSTRAINT TRIGGER check_condition AFTER INSERT OR UPDATE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_condition()")
        op.execute(f"CREATE CONSTRAINT TRIGGER check_review AFTER INSERT OR UPDATE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_section_review()")
    for table in ("patient_clinical_section_reviews", "patient_clinical_section_review_histories"):
        op.execute(f"CREATE CONSTRAINT TRIGGER check_review AFTER INSERT OR UPDATE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_section_review()")
    for table in ("patient_condition_histories", "patient_clinical_section_review_histories"):
        op.execute(f"CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.{table} FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_patient_condition() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_section_review() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.patient_conditions TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.patient_condition_histories TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT,UPDATE ON nightingale.patient_clinical_section_reviews TO nightingale_runtime")
    op.execute("GRANT SELECT,INSERT ON nightingale.patient_clinical_section_review_histories TO nightingale_runtime")


def downgrade():
    op.execute("DROP TABLE nightingale.patient_clinical_section_reviews CASCADE")
    op.execute("DROP TABLE nightingale.patient_clinical_section_review_histories")
    op.execute("DROP TABLE nightingale.patient_conditions CASCADE")
    op.execute("DROP TABLE nightingale.patient_condition_histories")
    op.execute("DROP FUNCTION nightingale.check_patient_condition()")
    op.execute("DROP FUNCTION nightingale.check_section_review()")
