"""Add patient billing review persistence: rates, grants, reports, evidence, reviews, payments and receipts."""

from alembic import op


revision = "20261127_03"
down_revision = "20261127_02"
branch_labels = None
depends_on = None

GRANTS = (
    ("billing_exchange_rates", "SELECT,INSERT"),
    ("patient_billing_grants", "SELECT,INSERT,UPDATE"),
    ("patient_payment_reports", "SELECT,INSERT,UPDATE"),
    ("patient_payment_evidence", "SELECT,INSERT"),
    ("billing_reviews", "SELECT,INSERT"),
    ("patient_payments", "SELECT,INSERT,UPDATE"),
    ("payment_receipts", "SELECT,INSERT"),
)


def upgrade():
    statements = """
        CREATE TABLE nightingale.billing_exchange_rates (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL,
            rate_date date NOT NULL,
            rate_ves_per_usd numeric(18,6) NOT NULL,
            source text NOT NULL,
            registered_by uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (account_id,rate_date),
            FOREIGN KEY (account_id) REFERENCES nightingale.accounts(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (registered_by) REFERENCES nightingale.app_users(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_billing_exchange_rates_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_billing_exchange_rates_rate_date_finite CHECK (isfinite(rate_date)),
            CONSTRAINT ck_billing_exchange_rates_rate CHECK (rate_ves_per_usd > 0),
            CONSTRAINT ck_billing_exchange_rates_source CHECK (btrim(source)<>''),
            CONSTRAINT ck_billing_exchange_rates_created_at_finite CHECK (isfinite(created_at))
        );

        CREATE TABLE nightingale.patient_billing_grants (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            appointment_id uuid,
            charge_id uuid,
            token_hash text NOT NULL UNIQUE,
            actions text[] NOT NULL,
            expires_at timestamptz NOT NULL,
            revoked_at timestamptz,
            created_by uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id,patient_id)
                REFERENCES nightingale.account_patients(account_id,patient_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (account_id,appointment_id,patient_id)
                REFERENCES nightingale.appointments(account_id,id,patient_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (charge_id,account_id)
                REFERENCES nightingale.patient_charges(id,account_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (created_by) REFERENCES nightingale.app_users(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_patient_billing_grants_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_patient_billing_grants_token_hash
                CHECK (token_hash ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_patient_billing_grants_actions CHECK (
                cardinality(actions) > 0
                AND actions <@ ARRAY['read_charge','submit_report','read_result','read_receipt']::text[]
            ),
            CONSTRAINT ck_patient_billing_grants_object
                CHECK (appointment_id IS NOT NULL OR charge_id IS NOT NULL),
            CONSTRAINT ck_patient_billing_grants_expires_at_finite CHECK (isfinite(expires_at)),
            CONSTRAINT ck_patient_billing_grants_revoked_at_finite
                CHECK (revoked_at IS NULL OR isfinite(revoked_at)),
            CONSTRAINT ck_patient_billing_grants_created_at_finite CHECK (isfinite(created_at))
        );
        CREATE INDEX ix_patient_billing_grants_patient
            ON nightingale.patient_billing_grants (account_id,patient_id);
        CREATE INDEX ix_patient_billing_grants_appointment
            ON nightingale.patient_billing_grants (appointment_id);

        CREATE TABLE nightingale.patient_payment_reports (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL,
            charge_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            grant_id uuid NOT NULL,
            status text NOT NULL DEFAULT 'pending',
            declared_paid_on date NOT NULL,
            declared_amount numeric(12,2) NOT NULL,
            declared_currency text NOT NULL,
            declared_method text NOT NULL,
            declared_reference_last4 text,
            declared_note text,
            previous_report_id uuid,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            version integer NOT NULL DEFAULT 1,
            CONSTRAINT uq_patient_payment_reports_id_account UNIQUE (id,account_id),
            FOREIGN KEY (charge_id,account_id)
                REFERENCES nightingale.patient_charges(id,account_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (account_id,patient_id)
                REFERENCES nightingale.account_patients(account_id,patient_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (grant_id) REFERENCES nightingale.patient_billing_grants(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (previous_report_id) REFERENCES nightingale.patient_payment_reports(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_patient_payment_reports_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_patient_payment_reports_status
                CHECK (status IN ('pending','approved','rejected')),
            CONSTRAINT ck_patient_payment_reports_paid_on_finite
                CHECK (isfinite(declared_paid_on)),
            CONSTRAINT ck_patient_payment_reports_amount CHECK (declared_amount > 0),
            CONSTRAINT ck_patient_payment_reports_currency
                CHECK (declared_currency IN ('USD','VES')),
            CONSTRAINT ck_patient_payment_reports_method CHECK (btrim(declared_method)<>''),
            CONSTRAINT ck_patient_payment_reports_reference_last4
                CHECK (declared_reference_last4 IS NULL
                    OR declared_reference_last4 ~ '^[0-9]{4}$'),
            CONSTRAINT ck_patient_payment_reports_note
                CHECK (declared_note IS NULL OR btrim(declared_note)<>''),
            CONSTRAINT ck_patient_payment_reports_created_at_finite CHECK (isfinite(created_at)),
            CONSTRAINT ck_patient_payment_reports_updated_at_finite CHECK (
                isfinite(updated_at) AND updated_at >= created_at
            ),
            CONSTRAINT ck_patient_payment_reports_version CHECK (version > 0)
        );
        CREATE INDEX ix_patient_payment_reports_inbox
            ON nightingale.patient_payment_reports (account_id,status,created_at);
        CREATE INDEX ix_patient_payment_reports_charge
            ON nightingale.patient_payment_reports (charge_id,created_at);

        CREATE TABLE nightingale.patient_payment_evidence (
            id uuid PRIMARY KEY,
            report_id uuid NOT NULL UNIQUE,
            storage_key text NOT NULL UNIQUE,
            content_type text NOT NULL,
            size_bytes integer NOT NULL,
            sha256 text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES nightingale.patient_payment_reports(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_patient_payment_evidence_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_patient_payment_evidence_storage_key CHECK (btrim(storage_key)<>''),
            CONSTRAINT ck_patient_payment_evidence_content_type CHECK (
                content_type IN ('image/jpeg','image/png','application/pdf')
            ),
            CONSTRAINT ck_patient_payment_evidence_size
                CHECK (size_bytes > 0 AND size_bytes <= 5242880),
            CONSTRAINT ck_patient_payment_evidence_sha256 CHECK (sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_patient_payment_evidence_created_at_finite
                CHECK (isfinite(created_at))
        );

        CREATE TABLE nightingale.billing_reviews (
            id uuid PRIMARY KEY,
            report_id uuid NOT NULL UNIQUE,
            account_id uuid NOT NULL,
            reviewer_id uuid NOT NULL,
            decision text NOT NULL,
            verified_paid_on date,
            verified_amount numeric(12,2),
            verified_currency text,
            billing_exchange_rate_id uuid,
            internal_note text,
            reason text,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id,account_id)
                REFERENCES nightingale.patient_payment_reports(id,account_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (reviewer_id) REFERENCES nightingale.app_users(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (billing_exchange_rate_id)
                REFERENCES nightingale.billing_exchange_rates(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_billing_reviews_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_billing_reviews_decision
                CHECK (decision IN ('approved','rejected')),
            CONSTRAINT ck_billing_reviews_paid_on_finite
                CHECK (verified_paid_on IS NULL OR isfinite(verified_paid_on)),
            CONSTRAINT ck_billing_reviews_amount
                CHECK (verified_amount IS NULL OR verified_amount > 0),
            CONSTRAINT ck_billing_reviews_currency
                CHECK (verified_currency IS NULL OR verified_currency IN ('USD','VES')),
            CONSTRAINT ck_billing_reviews_internal_note
                CHECK (internal_note IS NULL OR btrim(internal_note)<>''),
            CONSTRAINT ck_billing_reviews_reason
                CHECK (reason IS NULL OR btrim(reason)<>''),
            CONSTRAINT ck_billing_reviews_coherence CHECK (
                (decision='approved' AND verified_paid_on IS NOT NULL
                    AND verified_amount IS NOT NULL AND verified_currency IS NOT NULL)
                OR (decision='rejected' AND reason IS NOT NULL)
            ),
            CONSTRAINT ck_billing_reviews_created_at_finite CHECK (isfinite(created_at))
        );

        CREATE TABLE nightingale.patient_payments (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL,
            charge_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            origin text NOT NULL,
            origin_report_id uuid,
            amount numeric(14,2) NOT NULL,
            currency text NOT NULL,
            amount_usd numeric(12,2),
            exchange_rate numeric(18,6),
            exchange_rate_date date,
            exchange_rate_source text,
            paid_on date NOT NULL,
            method text NOT NULL,
            reference_last4 text,
            status text NOT NULL DEFAULT 'active',
            annulled_at timestamptz,
            annulled_by uuid,
            annulment_reason text,
            registered_by uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            version integer NOT NULL DEFAULT 1,
            CONSTRAINT uq_patient_payments_origin_report UNIQUE (origin_report_id),
            FOREIGN KEY (charge_id,account_id)
                REFERENCES nightingale.patient_charges(id,account_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (account_id,patient_id)
                REFERENCES nightingale.account_patients(account_id,patient_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (origin_report_id,account_id)
                REFERENCES nightingale.patient_payment_reports(id,account_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (annulled_by) REFERENCES nightingale.app_users(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (registered_by) REFERENCES nightingale.app_users(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_patient_payments_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_patient_payments_origin
                CHECK (origin IN ('patient_report','staff_entry')),
            CONSTRAINT ck_patient_payments_origin_coherence CHECK (
                (origin='patient_report' AND origin_report_id IS NOT NULL)
                OR (origin='staff_entry' AND origin_report_id IS NULL)
            ),
            CONSTRAINT ck_patient_payments_amount CHECK (amount > 0),
            CONSTRAINT ck_patient_payments_currency CHECK (currency IN ('USD','VES')),
            CONSTRAINT ck_patient_payments_conversion_coherence CHECK (
                (amount_usd IS NULL AND exchange_rate IS NULL
                    AND exchange_rate_date IS NULL AND exchange_rate_source IS NULL)
                OR (amount_usd IS NOT NULL AND amount_usd > 0
                    AND exchange_rate IS NOT NULL AND exchange_rate > 0
                    AND exchange_rate_date IS NOT NULL AND isfinite(exchange_rate_date)
                    AND exchange_rate_source IS NOT NULL AND btrim(exchange_rate_source)<>''
                    AND currency='USD')
            ),
            CONSTRAINT ck_patient_payments_paid_on_finite CHECK (isfinite(paid_on)),
            CONSTRAINT ck_patient_payments_method CHECK (btrim(method)<>''),
            CONSTRAINT ck_patient_payments_reference_last4
                CHECK (reference_last4 IS NULL OR reference_last4 ~ '^[0-9]{4}$'),
            CONSTRAINT ck_patient_payments_status CHECK (status IN ('active','annulled')),
            CONSTRAINT ck_patient_payments_annulment_coherence CHECK (
                (status='active' AND annulled_at IS NULL AND annulled_by IS NULL
                    AND annulment_reason IS NULL)
                OR (status='annulled' AND annulled_at IS NOT NULL
                    AND isfinite(annulled_at) AND annulled_by IS NOT NULL
                    AND annulment_reason IS NOT NULL AND btrim(annulment_reason)<>'')
            ),
            CONSTRAINT ck_patient_payments_created_at_finite CHECK (isfinite(created_at)),
            CONSTRAINT ck_patient_payments_updated_at_finite CHECK (
                isfinite(updated_at) AND updated_at >= created_at
            ),
            CONSTRAINT ck_patient_payments_version CHECK (version > 0)
        );
        CREATE INDEX ix_patient_payments_charge
            ON nightingale.patient_payments (account_id,charge_id,status);
        CREATE INDEX ix_patient_payments_account
            ON nightingale.patient_payments (account_id,created_at);

        CREATE TABLE nightingale.payment_receipts (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL,
            payment_id uuid NOT NULL UNIQUE,
            storage_key text NOT NULL UNIQUE,
            content_type text NOT NULL DEFAULT 'application/pdf',
            size_bytes integer NOT NULL,
            sha256 text NOT NULL,
            issued_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (payment_id) REFERENCES nightingale.patient_payments(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_payment_receipts_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_payment_receipts_storage_key CHECK (btrim(storage_key)<>''),
            CONSTRAINT ck_payment_receipts_content_type
                CHECK (content_type='application/pdf'),
            CONSTRAINT ck_payment_receipts_size CHECK (size_bytes > 0),
            CONSTRAINT ck_payment_receipts_sha256 CHECK (sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_payment_receipts_issued_at_finite CHECK (isfinite(issued_at))
        );
    """

    for statement in statements.split(";"):
        if statement.strip():
            op.execute(statement)

    for table, privileges in GRANTS:
        op.execute(f"GRANT {privileges} ON nightingale.{table} TO nightingale_runtime")


def downgrade():
    for table, privileges in GRANTS:
        op.execute(f"REVOKE {privileges} ON nightingale.{table} FROM nightingale_runtime")

    op.execute("DROP TABLE nightingale.payment_receipts")
    op.execute("DROP TABLE nightingale.patient_payments")
    op.execute("DROP TABLE nightingale.billing_reviews")
    op.execute("DROP TABLE nightingale.patient_payment_evidence")
    op.execute("DROP TABLE nightingale.patient_payment_reports")
    op.execute("DROP TABLE nightingale.patient_billing_grants")
    op.execute("DROP TABLE nightingale.billing_exchange_rates")
