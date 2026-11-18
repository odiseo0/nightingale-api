"""Care plans, goals, actions and reviews with immutable histories."""

from alembic import op

revision = "20261117_02"
down_revision = "20261117_01"
branch_labels = None
depends_on = None

DATE = "{name} text CHECK ({name} IS NULL OR {name}~'^\\d{4}(-\\d{2}(-\\d{2})?)?$')"
REASON = "{name} text CHECK ({name} IS NULL OR btrim({name})<>'')"
NONEMPTY = "{name} text NOT NULL CHECK (btrim({name})<>'')"


def upgrade():
    op.execute("""
        ALTER TABLE nightingale.account_memberships
        ADD COLUMN care_plans_access text NOT NULL DEFAULT 'read_write'
        CHECK (care_plans_access IN ('none','read','read_write'))
    """)
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
        ALTER TABLE nightingale.patient_conditions
        ADD CONSTRAINT patient_conditions_scoped_uq UNIQUE (account_id,id,patient_id)
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

    plan_body = f""",
            patient_id uuid NOT NULL,
            encounter_id uuid,
            condition_id uuid,
            {nonempty('title')},
            {reason('purpose')},
            {date('start_date')},
            {date('expected_end_date')},
            plan_status text NOT NULL DEFAULT 'active' CHECK (plan_status IN ('active','suspended','closed','cancelled')),
            {reason('status_reason')},
            captured_at_local timestamptz CHECK (captured_at_local IS NULL OR isfinite(captured_at_local)),
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.care_plans (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{plan_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            CHECK (plan_status='active' OR status_reason IS NOT NULL),
            FOREIGN KEY (account_id,patient_id) REFERENCES nightingale.account_patients(account_id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id) REFERENCES nightingale.clinical_encounters(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,condition_id,patient_id) REFERENCES nightingale.patient_conditions(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("care_plan_histories", "care_plans", plan_body.replace(
        "plan_status text NOT NULL DEFAULT 'active' CHECK", "plan_status text NOT NULL CHECK"
    ).replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_care_plans_list ON nightingale.care_plans(account_id,patient_id,plan_status,record_status,id)")
    guards("care_plans")

    goal_body = f""",
            patient_id uuid NOT NULL,
            plan_id uuid NOT NULL,
            {nonempty('description')},
            goal_kind text NOT NULL CHECK (goal_kind IN ('narrative','measurable')),
            measurement_kind text CHECK (measurement_kind IS NULL OR measurement_kind IN ('weight','temperature','oxygen_saturation','heart_rate','blood_pressure')),
            {reason('reference_description')},
            {reason('expected_result')},
            target_value numeric,
            {reason('unit')},
            {date('due_date')},
            evaluation_status text NOT NULL DEFAULT 'pending' CHECK (evaluation_status IN ('pending','achieved','not_achieved')),
            evaluated_at timestamptz CHECK (evaluated_at IS NULL OR isfinite(evaluated_at)),
            evaluated_by_user_id uuid,
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.care_plan_goals (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{goal_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            UNIQUE (account_id,id,patient_id),
            CHECK (goal_kind<>'measurable' OR (target_value IS NOT NULL OR unit IS NOT NULL OR measurement_kind IS NOT NULL)),
            CHECK (evaluation_status='pending' OR (evaluated_at IS NOT NULL AND evaluated_by_user_id IS NOT NULL)),
            FOREIGN KEY (account_id,plan_id,patient_id) REFERENCES nightingale.care_plans(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,evaluated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("care_plan_goal_histories", "care_plan_goals", goal_body.replace(
        "evaluation_status text NOT NULL DEFAULT 'pending' CHECK", "evaluation_status text NOT NULL CHECK"
    ).replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_care_plan_goals_list ON nightingale.care_plan_goals(account_id,plan_id,record_status,id)")
    guards("care_plan_goals")

    action_body = f""",
            patient_id uuid NOT NULL,
            plan_id uuid NOT NULL,
            goal_id uuid,
            {nonempty('description')},
            responsible_user_id uuid,
            {date('due_date')},
            completion_status text NOT NULL DEFAULT 'not_completed' CHECK (completion_status IN ('not_completed','completed')),
            completed_at timestamptz CHECK (completed_at IS NULL OR isfinite(completed_at)),
            {reason('completion_note')},
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.care_plan_actions (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{action_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            CHECK (completion_status<>'completed' OR completed_at IS NOT NULL),
            FOREIGN KEY (account_id,plan_id,patient_id) REFERENCES nightingale.care_plans(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,goal_id,patient_id) REFERENCES nightingale.care_plan_goals(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,responsible_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("care_plan_action_histories", "care_plan_actions", action_body.replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ).replace(
        "completion_status text NOT NULL DEFAULT 'not_completed' CHECK", "completion_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_care_plan_actions_list ON nightingale.care_plan_actions(account_id,plan_id,record_status,id)")
    guards("care_plan_actions")

    review_body = f""",
            patient_id uuid NOT NULL,
            plan_id uuid NOT NULL,
            reviewed_at timestamptz NOT NULL CHECK (isfinite(reviewed_at)),
            {nonempty('summary')},
            {reason('findings')},
            {date('next_review_date')},
            record_status text NOT NULL DEFAULT 'valid' CHECK (record_status IN ('valid','entered-in-error')),
            {reason('correction_reason')}{authors}"""

    op.execute(f"""
        CREATE TABLE nightingale.care_plan_reviews (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL{review_body},
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (account_id,id),
            FOREIGN KEY (account_id,plan_id,patient_id) REFERENCES nightingale.care_plans(account_id,id,patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,updated_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    history("care_plan_review_histories", "care_plan_reviews", review_body.replace(
        "record_status text NOT NULL DEFAULT 'valid' CHECK", "record_status text NOT NULL CHECK"
    ))
    op.execute("CREATE INDEX ix_care_plan_reviews_list ON nightingale.care_plan_reviews(account_id,plan_id,record_status,reviewed_at,id)")
    guards("care_plan_reviews")


def downgrade():
    for table in ("care_plan_review_histories", "care_plan_action_histories", "care_plan_goal_histories", "care_plan_histories"):
        op.execute(f"DROP TABLE nightingale.{table} CASCADE")
    for table in ("care_plan_reviews", "care_plan_actions", "care_plan_goals", "care_plans"):
        op.execute(f"DROP TABLE nightingale.{table} CASCADE")
    op.execute("ALTER TABLE nightingale.operation_receipts DROP CONSTRAINT operation_receipts_clinical_section_check")
    op.execute("""
        ALTER TABLE nightingale.operation_receipts
        ADD CONSTRAINT operation_receipts_clinical_section_check
        CHECK (clinical_section IN (
            'profile','conditions','allergies','encounters','notes',
            'measurements','immunizations','antecedents','declared_medications'
        ))
    """)
    op.execute("ALTER TABLE nightingale.change_log DROP CONSTRAINT change_log_audience_check")
    op.execute("""
        ALTER TABLE nightingale.change_log
        ADD CONSTRAINT change_log_audience_check
        CHECK (audience IN (
            'members','owner','clinical_profile','clinical_conditions','clinical_allergies',
            'clinical_encounters','clinical_notes','clinical_measurements',
            'clinical_immunizations','clinical_antecedents','clinical_declared_medications'
        ))
    """)
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_clinical_sections(value jsonb) RETURNS boolean
        LANGUAGE sql IMMUTABLE AS $$
            SELECT jsonb_typeof(value)='array'
                AND value <@ '["profile","conditions","allergies","encounters","notes","measurements","immunizations","antecedents","declared_medications"]'::jsonb
                AND (SELECT count(*)=count(DISTINCT item)
                    FROM jsonb_array_elements_text(value) AS section(item));
        $$
    """)
    op.execute("ALTER TABLE nightingale.patient_conditions DROP CONSTRAINT patient_conditions_scoped_uq")
    op.execute("ALTER TABLE nightingale.account_memberships DROP COLUMN care_plans_access")
