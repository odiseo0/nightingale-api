"""Account contacts and durable patient relationships."""

from alembic import op

revision = "20261026_04"
down_revision = "20261026_03"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(r"""
        CREATE TABLE nightingale.contact_people (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL REFERENCES nightingale.accounts(id) ON DELETE RESTRICT,
            full_name text NOT NULL CHECK (length(btrim(full_name))>0),
            phone_code text,
            phone text,
            issuing_country text CHECK (issuing_country ~ '^[A-Z]{2}$'),
            document_type text COLLATE "C" CHECK (document_type IN ('national_id','passport')),
            document_number text COLLATE "C" CHECK (length(btrim(document_number))>0),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            CHECK ((phone_code IS NULL AND phone IS NULL) OR
                (phone_code IS NOT NULL AND phone IS NOT NULL AND phone_code ~ '^\+[1-9][0-9]{0,2}$' AND phone ~ '^[0-9]+$')),
            CHECK ((issuing_country IS NULL AND document_type IS NULL AND document_number IS NULL) OR
                (issuing_country IS NOT NULL AND document_type IS NOT NULL AND document_number IS NOT NULL))
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.patient_contact_relationships (
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            contact_person_id uuid NOT NULL,
            relationship_kind text NOT NULL CHECK (relationship_kind IN ('mother','father','guardian','other')),
            is_responsible_contact boolean NOT NULL DEFAULT false,
            representation_status text NOT NULL DEFAULT 'unverified' CHECK (representation_status IN ('unverified','verified')),
            verified_at timestamptz,
            verified_by_user_id uuid,
            valid_from timestamptz NOT NULL CHECK (isfinite(valid_from)),
            valid_until timestamptz CHECK (valid_until IS NULL OR (isfinite(valid_until) AND valid_until>valid_from)),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            PRIMARY KEY (account_id,patient_id,contact_person_id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,contact_person_id) REFERENCES nightingale.contact_people(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,verified_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            CHECK ((representation_status='unverified' AND verified_at IS NULL AND verified_by_user_id IS NULL) OR
                (representation_status='verified' AND verified_at IS NOT NULL AND verified_by_user_id IS NOT NULL AND
                    isfinite(verified_at) AND verified_at>=created_at AND verified_at<=updated_at))
        )
    """)
    op.execute("CREATE INDEX ix_contact_people_state ON nightingale.contact_people(account_id,status)")
    op.execute("CREATE INDEX ix_patient_contacts_contact ON nightingale.patient_contact_relationships(account_id,contact_person_id,patient_id)")
    op.execute("CREATE INDEX ix_patient_contacts_verifier ON nightingale.patient_contact_relationships(account_id,verified_by_user_id)")
    op.execute("""
        CREATE FUNCTION nightingale.guard_patient_contact() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.account_id IS DISTINCT FROM OLD.account_id OR NEW.created_at IS DISTINCT FROM OLD.created_at
                OR NEW.updated_at<OLD.updated_at OR NEW.version<>OLD.version+1 THEN
                RAISE EXCEPTION 'Contact account, times or version are invalid' USING ERRCODE='23514';
            END IF;
            IF TG_TABLE_NAME='contact_people' THEN
                IF NEW.id IS DISTINCT FROM OLD.id THEN
                    RAISE EXCEPTION 'Contact identity is immutable' USING ERRCODE='23514';
                END IF;
            ELSE
                IF (NEW.patient_id,NEW.contact_person_id) IS DISTINCT FROM (OLD.patient_id,OLD.contact_person_id) OR
                    (OLD.representation_status='verified' AND
                        (NEW.representation_status,NEW.verified_at,NEW.verified_by_user_id) IS DISTINCT FROM
                        (OLD.representation_status,OLD.verified_at,OLD.verified_by_user_id)) OR
                    (OLD.representation_status='unverified' AND NEW.representation_status='unverified' AND
                        (NEW.verified_at IS NOT NULL OR NEW.verified_by_user_id IS NOT NULL)) THEN
                    RAISE EXCEPTION 'Relationship identity or evidence is immutable' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NEW;
        END; $$
    """)
    for table in ("contact_people", "patient_contact_relationships"):
        op.execute(f"CREATE TRIGGER guard_patient_contact BEFORE UPDATE ON nightingale.{table} FOR EACH ROW EXECUTE FUNCTION nightingale.guard_patient_contact()")
        op.execute(f"GRANT SELECT,INSERT,UPDATE ON nightingale.{table} TO nightingale_runtime")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_patient_contact() FROM PUBLIC")


def downgrade():
    op.execute("DROP TABLE nightingale.patient_contact_relationships")
    op.execute("DROP TABLE nightingale.contact_people")
    op.execute("DROP FUNCTION nightingale.guard_patient_contact()")
