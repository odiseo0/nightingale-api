"""Diagnostic reports, structured results and private attachment metadata."""

from alembic import op

revision = "20261117_03"
down_revision = "20261117_02"
branch_labels = None
depends_on = None

DATE = "{name} text CHECK ({name} IS NULL OR {name}~'^\\d{4}(-\\d{2}(-\\d{2})?)?$')"
REASON = "{name} text CHECK ({name} IS NULL OR btrim({name})<>'')"
NONEMPTY = "{name} text NOT NULL CHECK (btrim({name})<>'')"


def upgrade():
    op.execute("""
        ALTER TABLE nightingale.account_memberships
        ADD COLUMN diagnostic_reports_access text NOT NULL DEFAULT 'read_write'
        CHECK (diagnostic_reports_access IN ('none','read','read_write'))
    """)
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

    date = lambda name: DATE.replace("{name}", name)  # noqa: E731
    reason = lambda name: REASON.replace("{name}", name)  # noqa: E731
    nonempty = lambda name: NONEMPTY.replace("{name}", name)  # noqa: E731

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

    report_body = f""",
            patient_id uuid NOT NULL,
            encounter_id uuid,
            {nonempty('source_name')},
            source_type text NOT NULL DEFAULT 'unknown' CHECK (source_type IN ('patient','related_person','professional','external_document','unknown')),
            {date('sample_date')},
            {date('issued_date')},
            report_kind text NOT NULL CHECK (report_kind IN ('laboratory','imaging','pathology','other')),
            report_status text NOT NULL CHECK (report_status IN ('preliminary','final')),
            attachment_id uuid,
            {reason('clinical_summary')},
            captured_at_local timestamptz CHECK (captured_at_local IS NULL OR isfinite(captured_at_local)),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.diagnostic_reports (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{report_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id) REFERENCES nightingale.clinical_encounters(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("diagnostic_report_histories", "diagnostic_reports", report_body.replace(
        "source_type text NOT NULL DEFAULT 'unknown' CHECK", "source_type text NOT NULL CHECK"
    ).replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_diagnostic_reports_list ON nightingale.diagnostic_reports(account_id,patient_id,record_status,sample_date,id)")
    op.execute("CREATE INDEX ix_diagnostic_reports_encounter ON nightingale.diagnostic_reports(account_id,encounter_id,patient_id)")
    guards("diagnostic_reports")

    result_body = f""",
            patient_id uuid NOT NULL,
            report_id uuid NOT NULL,
            {nonempty('analyte_name')},
            result_kind text NOT NULL CHECK (result_kind IN ('numeric','text')),
            value numeric,
            {reason('text_value')},
            {reason('unit')},
            reference_low numeric,
            reference_high numeric,
            {reason('reference_text')},
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.diagnostic_report_results (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{result_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            CHECK (result_kind<>'numeric' OR (value IS NOT NULL AND unit IS NOT NULL AND text_value IS NULL)),
            CHECK (result_kind<>'text' OR (text_value IS NOT NULL AND value IS NULL AND unit IS NULL)),
            CHECK ((reference_low IS NULL AND reference_high IS NULL) OR reference_text IS NULL),
            CHECK (reference_high IS NULL OR reference_low IS NULL OR reference_high>=reference_low),
            FOREIGN KEY (account_id,report_id,patient_id) REFERENCES nightingale.diagnostic_reports(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("diagnostic_report_result_histories", "diagnostic_report_results", result_body.replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_diagnostic_report_results_list ON nightingale.diagnostic_report_results(account_id,report_id,record_status,id)")
    guards("diagnostic_report_results")

    attachment_body = f""",
            patient_id uuid NOT NULL,
            {nonempty('file_name')},
            {nonempty('content_type')},
            byte_size bigint NOT NULL CHECK (byte_size>0),
            sha256 text NOT NULL CHECK (sha256~'^[0-9a-f]{{64}}$'),
            {nonempty('storage_key')},
            uploaded_at timestamptz NOT NULL CHECK (isfinite(uploaded_at)),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.report_attachments (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{attachment_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("report_attachment_histories", "report_attachments", attachment_body.replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_report_attachments_list ON nightingale.report_attachments(account_id,patient_id,record_status,id)")
    op.execute("CREATE UNIQUE INDEX uq_report_attachments_storage_key ON nightingale.report_attachments(account_id,sha256)")
    guards("report_attachments")


def downgrade():
    for table in ("report_attachment_histories", "diagnostic_report_result_histories", "diagnostic_report_histories"):
        op.execute(f"DROP TABLE nightingale.{table} CASCADE")
    for table in ("report_attachments", "diagnostic_report_results", "diagnostic_reports"):
        op.execute(f"DROP TABLE nightingale.{table} CASCADE")
    op.execute("ALTER TABLE nightingale.operation_receipts DROP CONSTRAINT operation_receipts_clinical_section_check")
    op.execute("""
        ALTER TABLE nightingale.operation_receipts
        ADD CONSTRAINT operation_receipts_clinical_section_check
        CHECK (clinical_section IN (
            'profile','conditions','allergies','encounters','notes',
            'measurements','immunizations','antecedents','declared_medications','care_plans'
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
            'clinical_care_plans'
        ))
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_clinical_sections(value jsonb) RETURNS boolean
        LANGUAGE sql IMMUTABLE AS $$
            SELECT jsonb_typeof(value)='array'
                AND value <@ '["profile","conditions","allergies","encounters","notes","measurements","immunizations","antecedents","declared_medications","care_plans"]'::jsonb
                AND (SELECT count(*)=count(DISTINCT item)
                    FROM jsonb_array_elements_text(value) AS section(item));
        $$
    """)
    op.execute("ALTER TABLE nightingale.account_memberships DROP COLUMN diagnostic_reports_access")
