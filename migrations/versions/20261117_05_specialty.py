"""Odontogram findings and treatments for the first specialty (dentistry)."""

from alembic import op

revision = "20261117_05"
down_revision = "20261117_04"
branch_labels = None
depends_on = None

DATE = "{name} text CHECK ({name} IS NULL OR {name}~'^\\d{4}(-\\d{2}(-\\d{2})?)?$')"
REASON = "{name} text CHECK ({name} IS NULL OR btrim({name})<>'')"
NONEMPTY = "{name} text NOT NULL CHECK (btrim({name})<>'')"

FDI_CHECK = (
    "((tooth_fdi BETWEEN 11 AND 48 AND tooth_fdi%10 BETWEEN 1 AND 8) "
    "OR (tooth_fdi BETWEEN 51 AND 85 AND tooth_fdi%10 BETWEEN 1 AND 5))"
)


def upgrade():
    nonempty = lambda name: NONEMPTY.replace("{name}", name)  # noqa: E731
    reason = lambda name: REASON.replace("{name}", name)  # noqa: E731
    date = lambda name: DATE.replace("{name}", name)  # noqa: E731

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

    finding_body = f""",
            patient_id uuid NOT NULL,
            encounter_id uuid,
            tooth_fdi smallint NOT NULL CHECK ({FDI_CHECK}),
            surface text CHECK (surface IS NULL OR surface IN ('vestibular','palatina','lingual','mesial','distal','oclusal','incisal','cervical')),
            finding_kind text NOT NULL CHECK (finding_kind IN ('healthy','caries','missing','filling','crown','fracture','other')),
            finding_status text NOT NULL DEFAULT 'active' CHECK (finding_status IN ('active','resolved')),
            {reason('note')},
            {date('recorded_date')},
            captured_at_local timestamptz CHECK (captured_at_local IS NULL OR isfinite(captured_at_local)),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.dental_findings (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{finding_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id) REFERENCES nightingale.clinical_encounters(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("dental_finding_histories", "dental_findings", finding_body.replace(
        "finding_status text NOT NULL DEFAULT 'active' CHECK", "finding_status text NOT NULL CHECK"
    ).replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_dental_findings_list ON nightingale.dental_findings(account_id,patient_id,tooth_fdi,surface,id)")
    op.execute("CREATE UNIQUE INDEX uq_dental_findings_active ON nightingale.dental_findings(account_id,patient_id,tooth_fdi,surface,finding_kind) WHERE record_status='valid' AND finding_status='active'")
    guards("dental_findings")

    treatment_body = f""",
            patient_id uuid NOT NULL,
            finding_id uuid NOT NULL,
            treatment_kind text NOT NULL CHECK (treatment_kind IN ('cleaning','filling','crown','extraction','other')),
            treatment_status text NOT NULL DEFAULT 'planned' CHECK (treatment_status IN ('planned','performed')),
            {reason('note')},
            {date('performed_date')},
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.dental_treatments (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{treatment_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            CHECK (treatment_status<>'performed' OR performed_date IS NOT NULL),
            FOREIGN KEY (account_id,finding_id,patient_id) REFERENCES nightingale.dental_findings(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("dental_treatment_histories", "dental_treatments", treatment_body.replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ).replace(
        "treatment_status text NOT NULL DEFAULT 'planned' CHECK", "treatment_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_dental_treatments_list ON nightingale.dental_treatments(account_id,finding_id,record_status,id)")
    guards("dental_treatments")


def downgrade():
    for table in ("dental_treatment_histories", "dental_finding_histories"):
        op.execute(f"DROP TABLE nightingale.{table} CASCADE")
    for table in ("dental_treatments", "dental_findings"):
        op.execute(f"DROP TABLE nightingale.{table} CASCADE")
