"""Specialty templates, versioned fields and typed-value records."""

from alembic import op

revision = "20261117_04"
down_revision = "20261117_03"
branch_labels = None
depends_on = None

REASON = "{name} text CHECK ({name} IS NULL OR btrim({name})<>'')"
NONEMPTY = "{name} text NOT NULL CHECK (btrim({name})<>'')"


def upgrade():
    op.execute("""
        ALTER TABLE nightingale.account_memberships
        ADD COLUMN specialty_templates_access text NOT NULL DEFAULT 'read_write'
        CHECK (specialty_templates_access IN ('none','read','read_write'))
    """)
    op.execute("ALTER TABLE nightingale.operation_receipts DROP CONSTRAINT operation_receipts_clinical_section_check")
    op.execute("""
        ALTER TABLE nightingale.operation_receipts
        ADD CONSTRAINT operation_receipts_clinical_section_check
        CHECK (clinical_section IN (
            'profile','conditions','allergies','encounters','notes',
            'measurements','immunizations','antecedents','declared_medications','care_plans',
            'diagnostic_reports','specialty_templates'
        ))
    """)
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute("""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN (
            'members','owner','clinical_profile','clinical_conditions','clinical_allergies',
            'clinical_encounters','clinical_notes','clinical_measurements',
            'clinical_immunizations','clinical_antecedents','clinical_declared_medications',
            'clinical_care_plans','clinical_diagnostic_reports','clinical_specialty_templates'
        ))
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_clinical_sections(value jsonb) RETURNS boolean
        LANGUAGE sql IMMUTABLE AS $$
            SELECT jsonb_typeof(value)='array'
                AND value <@ '["profile","conditions","allergies","encounters","notes","measurements","immunizations","antecedents","declared_medications","care_plans","diagnostic_reports","specialty_templates"]'::jsonb
                AND (SELECT count(*)=count(DISTINCT item)
                    FROM jsonb_array_elements_text(value) AS section(item));
        $$
    """)

    nonempty = lambda name: NONEMPTY.replace("{name}", name)  # noqa: E731
    reason = lambda name: REASON.replace("{name}", name)  # noqa: E731

    authors = """,
            created_by_user_id uuid NOT NULL,
            updated_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at)"""

    history_tail = """
            version integer NOT NULL CHECK (version>0),
            action text NOT NULL CHECK (action IN ('created','updated','invalidated')),
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            changed_at timestamptz NOT NULL CHECK (isfinite(changed_at)),
            PRIMARY KEY (account_id,id,version)"""

    def history(table, source, body):
        body = body.lstrip().removeprefix(",").lstrip()
        op.execute(f"""
            CREATE TABLE nightingale.{table} (
                account_id uuid NOT NULL,
                id uuid NOT NULL,
{body},
{history_tail},
                FOREIGN KEY (account_id,id) REFERENCES nightingale.{source}(account_id,id) ON DELETE RESTRICT,
                FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
            )
        """)
        op.execute(
            f"ALTER TABLE nightingale.{source} ADD CONSTRAINT {source}_current_version "
            f"FOREIGN KEY (account_id,id,version) REFERENCES nightingale.{table}(account_id,id,version) "
            "DEFERRABLE INITIALLY DEFERRED"
        )
        op.execute(f"CREATE TRIGGER guard_history BEFORE UPDATE OR DELETE ON nightingale.{table} FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_history()")
        op.execute(f"CREATE INDEX ix_{table}_receipt ON nightingale.{table}(account_id,actor_user_id,operation_id)")
        op.execute(f"GRANT SELECT,INSERT ON nightingale.{table} TO nightingale_runtime")

    def guards(table):
        op.execute(f"CREATE TRIGGER guard_clinical_identity BEFORE UPDATE ON nightingale.{table} FOR EACH ROW EXECUTE FUNCTION nightingale.guard_clinical_identity()")
        op.execute(f"GRANT SELECT,INSERT,UPDATE ON nightingale.{table} TO nightingale_runtime")


    template_body = f""",
            {nonempty('name')},
            specialty text NOT NULL DEFAULT 'dentistry' CHECK (specialty IN ('dentistry')),
            template_status text NOT NULL DEFAULT 'active' CHECK (template_status IN ('active','retired')),
            {reason('change_note')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.specialty_templates (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{template_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            FOREIGN KEY (account_id) REFERENCES nightingale.accounts(id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("specialty_template_histories", "specialty_templates", template_body.replace(
        "specialty text NOT NULL DEFAULT 'dentistry' CHECK", "specialty text NOT NULL CHECK"
    ).replace(
        "template_status text NOT NULL DEFAULT 'active' CHECK", "template_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_specialty_templates_list ON nightingale.specialty_templates(account_id,template_status,id)")
    guards("specialty_templates")
    op.execute("""
        CREATE FUNCTION nightingale.guard_template_identity() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.account_id IS DISTINCT FROM OLD.account_id
                OR NEW.id IS DISTINCT FROM OLD.id THEN
                RAISE EXCEPTION 'Template identity is immutable' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("DROP TRIGGER guard_clinical_identity ON nightingale.specialty_templates")
    op.execute("CREATE TRIGGER guard_template_identity BEFORE UPDATE ON nightingale.specialty_templates FOR EACH ROW EXECUTE FUNCTION nightingale.guard_template_identity()")

    op.execute("""
        CREATE TABLE nightingale.specialty_template_fields (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            template_id uuid NOT NULL,
            template_version integer NOT NULL CHECK (template_version>0),
            field_key text NOT NULL CHECK (btrim(field_key)<>'' AND field_key NOT LIKE '%|%'),
            label text NOT NULL CHECK (btrim(label)<>''),
            field_kind text NOT NULL CHECK (field_kind IN ('text','number','boolean','date_partial')),
            required boolean NOT NULL DEFAULT false,
            options text CHECK (options IS NULL OR btrim(options)<>''),
            display_order integer NOT NULL CHECK (display_order>0),
            UNIQUE (account_id,template_id,template_version,field_key),
            UNIQUE (account_id,template_id,template_version,display_order),
            FOREIGN KEY (account_id,template_id) REFERENCES nightingale.specialty_templates(account_id,id) ON DELETE RESTRICT
        )
    """)
    op.execute("GRANT SELECT,INSERT,DELETE ON nightingale.specialty_template_fields TO nightingale_runtime")

    record_body = f""",
            patient_id uuid NOT NULL,
            encounter_id uuid,
            template_id uuid NOT NULL,
            template_version integer NOT NULL CHECK (template_version>0),
            recorded_at timestamptz NOT NULL CHECK (isfinite(recorded_at)),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.specialty_records (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{record_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id) REFERENCES nightingale.clinical_encounters(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,template_id) REFERENCES nightingale.specialty_templates(account_id,id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("specialty_record_histories", "specialty_records", record_body.replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_specialty_records_list ON nightingale.specialty_records(account_id,patient_id,record_status,id)")
    guards("specialty_records")

    op.execute("""
        CREATE TABLE nightingale.specialty_record_values (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            record_id uuid NOT NULL,
            record_version integer NOT NULL CHECK (record_version>0),
            field_key text NOT NULL CHECK (btrim(field_key)<>''),
            value_text text CHECK (value_text IS NULL OR btrim(value_text)<>''),
            value_number numeric,
            value_boolean boolean,
            value_date text CHECK (value_date IS NULL OR value_date~'^\\d{4}(-\\d{2}(-\\d{2})?)?$'),
            UNIQUE (account_id,record_id,record_version,field_key),
            CHECK ((value_text IS NOT NULL)::integer + (value_number IS NOT NULL)::integer
                 + (value_boolean IS NOT NULL)::integer + (value_date IS NOT NULL)::integer = 1),
            FOREIGN KEY (account_id,record_id,patient_id) REFERENCES nightingale.specialty_records(account_id,id,patient_id) ON DELETE RESTRICT
        )
    """)
    op.execute("GRANT SELECT,INSERT,DELETE ON nightingale.specialty_record_values TO nightingale_runtime")


def downgrade():
    op.execute("DROP TRIGGER guard_template_identity ON nightingale.specialty_templates")
    op.execute("DROP FUNCTION nightingale.guard_template_identity()")
    for table in ("specialty_record_values", "specialty_template_fields"):
        op.execute(f"DROP TABLE nightingale.{table} CASCADE")
    for table in ("specialty_record_histories", "specialty_template_histories"):
        op.execute(f"DROP TABLE nightingale.{table} CASCADE")
    for table in ("specialty_records", "specialty_templates"):
        op.execute(f"DROP TABLE nightingale.{table} CASCADE")
    op.execute("ALTER TABLE nightingale.operation_receipts DROP CONSTRAINT operation_receipts_clinical_section_check")
    op.execute("""
        ALTER TABLE nightingale.operation_receipts
        ADD CONSTRAINT operation_receipts_clinical_section_check
        CHECK (clinical_section IN (
            'profile','conditions','allergies','encounters','notes',
            'measurements','immunizations','antecedents','declared_medications','care_plans',
            'diagnostic_reports'
        ))
    """)
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute("""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN (
            'members','owner','clinical_profile','clinical_conditions','clinical_allergies',
            'clinical_encounters','clinical_notes','clinical_measurements',
            'clinical_immunizations','clinical_antecedents','clinical_declared_medications',
            'clinical_care_plans','clinical_diagnostic_reports'
        ))
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_clinical_sections(value jsonb) RETURNS boolean
        LANGUAGE sql IMMUTABLE AS $$
            SELECT jsonb_typeof(value)='array'
                AND value <@ '["profile","conditions","allergies","encounters","notes","measurements","immunizations","antecedents","declared_medications","care_plans","diagnostic_reports"]'::jsonb
                AND (SELECT count(*)=count(DISTINCT item)
                    FROM jsonb_array_elements_text(value) AS section(item));
        $$
    """)
    op.execute("ALTER TABLE nightingale.account_memberships DROP COLUMN specialty_templates_access")
