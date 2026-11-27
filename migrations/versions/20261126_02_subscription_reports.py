"""Add subscription review persistence: operators, rates, reports, evidence and reviews."""

from alembic import op


revision = "20261126_02"
down_revision = "20261126_01"
branch_labels = None
depends_on = None

GRANTS = (
    ("platform_operators", "SELECT,INSERT,UPDATE"),
    ("platform_operator_credentials", "SELECT,INSERT,UPDATE"),
    ("bcv_exchange_rates", "SELECT,INSERT"),
    ("payment_reports", "SELECT,INSERT,UPDATE"),
    ("payment_report_evidence", "SELECT,INSERT"),
    ("subscription_reviews", "SELECT,INSERT"),
)


def upgrade():
    statements = """
        CREATE TABLE nightingale.platform_operators (
            id uuid PRIMARY KEY,
            oidc_issuer text NOT NULL,
            oidc_subject text NOT NULL,
            display_name text NOT NULL,
            actions text[] NOT NULL,
            status text NOT NULL DEFAULT 'active',
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            version integer NOT NULL DEFAULT 1,
            UNIQUE (oidc_issuer,oidc_subject),
            CONSTRAINT ck_platform_operators_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_platform_operators_display_name CHECK (btrim(display_name)<>''),
            CONSTRAINT ck_platform_operators_actions CHECK (
                cardinality(actions) > 0
                AND actions <@ ARRAY['review','catalog','rates','operators']::text[]
            ),
            CONSTRAINT ck_platform_operators_status CHECK (status IN ('active','revoked')),
            CONSTRAINT ck_platform_operators_created_at_finite CHECK (isfinite(created_at)),
            CONSTRAINT ck_platform_operators_updated_at_finite CHECK (
                isfinite(updated_at) AND updated_at >= created_at
            ),
            CONSTRAINT ck_platform_operators_version CHECK (version > 0)
        );

        CREATE TABLE nightingale.platform_operator_credentials (
            id uuid PRIMARY KEY,
            operator_id uuid NOT NULL,
            token_hash text NOT NULL UNIQUE,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            revoked_at timestamptz,
            FOREIGN KEY (operator_id) REFERENCES nightingale.platform_operators(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_platform_operator_credentials_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_platform_operator_credentials_token_hash
                CHECK (token_hash ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_platform_operator_credentials_created_at_finite
                CHECK (isfinite(created_at)),
            CONSTRAINT ck_platform_operator_credentials_revoked_at_finite
                CHECK (revoked_at IS NULL OR isfinite(revoked_at))
        );
        CREATE INDEX ix_platform_operator_credentials_operator
            ON nightingale.platform_operator_credentials (operator_id);

        CREATE TABLE nightingale.bcv_exchange_rates (
            id uuid PRIMARY KEY,
            rate_date date NOT NULL UNIQUE,
            rate_ves_per_usd numeric(18,6) NOT NULL,
            source text NOT NULL,
            registered_by uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (registered_by) REFERENCES nightingale.platform_operators(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_bcv_exchange_rates_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_bcv_exchange_rates_rate_date_finite CHECK (isfinite(rate_date)),
            CONSTRAINT ck_bcv_exchange_rates_rate CHECK (rate_ves_per_usd > 0),
            CONSTRAINT ck_bcv_exchange_rates_source CHECK (btrim(source)<>''),
            CONSTRAINT ck_bcv_exchange_rates_created_at_finite CHECK (isfinite(created_at))
        );

        ALTER TABLE nightingale.account_subscriptions
            ADD CONSTRAINT uq_account_subscriptions_id_account UNIQUE (id,account_id);

        CREATE TABLE nightingale.payment_reports (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL,
            subscription_id uuid NOT NULL,
            plan_version_id uuid NOT NULL,
            periodicity text NOT NULL,
            status text NOT NULL DEFAULT 'pending',
            declared_paid_on date NOT NULL,
            declared_amount numeric(12,2) NOT NULL,
            declared_currency text NOT NULL,
            declared_method text NOT NULL,
            declared_reference_last4 text,
            declared_note text,
            previous_report_id uuid,
            submitted_by uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            version integer NOT NULL DEFAULT 1,
            FOREIGN KEY (account_id) REFERENCES nightingale.accounts(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (subscription_id,account_id)
                REFERENCES nightingale.account_subscriptions(id,account_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (plan_version_id)
                REFERENCES nightingale.subscription_plan_versions(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (previous_report_id) REFERENCES nightingale.payment_reports(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (submitted_by) REFERENCES nightingale.app_users(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_payment_reports_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_payment_reports_periodicity
                CHECK (periodicity IN ('days_30','year_1')),
            CONSTRAINT ck_payment_reports_status
                CHECK (status IN ('pending','approved','rejected')),
            CONSTRAINT ck_payment_reports_paid_on_finite CHECK (isfinite(declared_paid_on)),
            CONSTRAINT ck_payment_reports_amount CHECK (declared_amount > 0),
            CONSTRAINT ck_payment_reports_currency CHECK (declared_currency IN ('VES','USD')),
            CONSTRAINT ck_payment_reports_method CHECK (btrim(declared_method)<>''),
            CONSTRAINT ck_payment_reports_reference_last4
                CHECK (declared_reference_last4 IS NULL OR declared_reference_last4 ~ '^[0-9]{4}$'),
            CONSTRAINT ck_payment_reports_note
                CHECK (declared_note IS NULL OR btrim(declared_note)<>''),
            CONSTRAINT ck_payment_reports_created_at_finite CHECK (isfinite(created_at)),
            CONSTRAINT ck_payment_reports_updated_at_finite CHECK (
                isfinite(updated_at) AND updated_at >= created_at
            ),
            CONSTRAINT ck_payment_reports_version CHECK (version > 0)
        );
        CREATE INDEX ix_payment_reports_account
            ON nightingale.payment_reports (account_id,created_at);
        CREATE INDEX ix_payment_reports_status
            ON nightingale.payment_reports (status,created_at);

        CREATE TABLE nightingale.payment_report_evidence (
            id uuid PRIMARY KEY,
            report_id uuid NOT NULL UNIQUE,
            storage_key text NOT NULL UNIQUE,
            content_type text NOT NULL,
            size_bytes integer NOT NULL,
            sha256 text NOT NULL,
            uploaded_by uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES nightingale.payment_reports(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (uploaded_by) REFERENCES nightingale.app_users(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_payment_report_evidence_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_payment_report_evidence_storage_key CHECK (btrim(storage_key)<>''),
            CONSTRAINT ck_payment_report_evidence_content_type CHECK (
                content_type IN ('image/jpeg','image/png','application/pdf')
            ),
            CONSTRAINT ck_payment_report_evidence_size
                CHECK (size_bytes > 0 AND size_bytes <= 5242880),
            CONSTRAINT ck_payment_report_evidence_sha256 CHECK (sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_payment_report_evidence_created_at_finite
                CHECK (isfinite(created_at))
        );

        CREATE TABLE nightingale.subscription_reviews (
            id uuid PRIMARY KEY,
            report_id uuid NOT NULL UNIQUE,
            operator_id uuid NOT NULL,
            decision text NOT NULL,
            verified_paid_on date,
            verified_amount numeric(12,2),
            verified_currency text,
            bcv_rate_id uuid,
            reason text,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES nightingale.payment_reports(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (operator_id) REFERENCES nightingale.platform_operators(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (bcv_rate_id) REFERENCES nightingale.bcv_exchange_rates(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_subscription_reviews_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_subscription_reviews_decision
                CHECK (decision IN ('approved','rejected')),
            CONSTRAINT ck_subscription_reviews_paid_on_finite
                CHECK (verified_paid_on IS NULL OR isfinite(verified_paid_on)),
            CONSTRAINT ck_subscription_reviews_amount
                CHECK (verified_amount IS NULL OR verified_amount > 0),
            CONSTRAINT ck_subscription_reviews_currency
                CHECK (verified_currency IS NULL OR verified_currency IN ('VES','USD')),
            CONSTRAINT ck_subscription_reviews_reason
                CHECK (reason IS NULL OR btrim(reason)<>''),
            CONSTRAINT ck_subscription_reviews_coherence CHECK (
                (decision='approved' AND verified_paid_on IS NOT NULL
                    AND verified_amount IS NOT NULL AND verified_currency IS NOT NULL)
                OR (decision='rejected' AND reason IS NOT NULL)
            ),
            CONSTRAINT ck_subscription_reviews_created_at_finite CHECK (isfinite(created_at))
        );

        ALTER TABLE nightingale.subscription_periods
            ADD COLUMN origin_review_id uuid NOT NULL,
            ADD CONSTRAINT fk_subscription_periods_origin_review
                FOREIGN KEY (origin_review_id)
                REFERENCES nightingale.subscription_reviews(id) ON DELETE RESTRICT,
            ADD CONSTRAINT uq_subscription_periods_origin_review UNIQUE (origin_review_id);
    """

    for statement in statements.split(";"):
        if statement.strip():
            op.execute(statement)

    for table, privileges in GRANTS:
        op.execute(f"GRANT {privileges} ON nightingale.{table} TO nightingale_runtime")


def downgrade():
    for table, privileges in GRANTS:
        op.execute(f"REVOKE {privileges} ON nightingale.{table} FROM nightingale_runtime")

    op.execute("""
        ALTER TABLE nightingale.subscription_periods
            DROP CONSTRAINT uq_subscription_periods_origin_review,
            DROP CONSTRAINT fk_subscription_periods_origin_review,
            DROP COLUMN origin_review_id
    """)
    op.execute("DROP TABLE nightingale.subscription_reviews")
    op.execute("DROP TABLE nightingale.payment_report_evidence")
    op.execute("DROP TABLE nightingale.payment_reports")
    op.execute(
        "ALTER TABLE nightingale.account_subscriptions "
        "DROP CONSTRAINT uq_account_subscriptions_id_account"
    )
    op.execute("DROP TABLE nightingale.bcv_exchange_rates")
    op.execute("DROP TABLE nightingale.platform_operator_credentials")
    op.execute("DROP TABLE nightingale.platform_operators")
