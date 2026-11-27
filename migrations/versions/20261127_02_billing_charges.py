"""Add patient billing core: service prices, charges and charge histories."""

from alembic import op


revision = "20261127_02"
down_revision = "20261127_01"
branch_labels = None
depends_on = None

GRANTS = (
    ("service_prices", "SELECT,INSERT,UPDATE,DELETE"),
    ("service_offer_prices", "SELECT,INSERT,UPDATE,DELETE"),
    ("patient_charges", "SELECT,INSERT,UPDATE"),
    ("charge_histories", "SELECT,INSERT"),
)


def upgrade():
    statements = """
        CREATE TABLE nightingale.service_prices (
            professional_id uuid NOT NULL,
            service_id uuid NOT NULL,
            amount numeric(12,2) NOT NULL,
            currency text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            version integer NOT NULL DEFAULT 1,
            PRIMARY KEY (professional_id,service_id),
            FOREIGN KEY (professional_id,service_id)
                REFERENCES nightingale.services(professional_id,id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_service_prices_amount CHECK (amount >= 0),
            CONSTRAINT ck_service_prices_currency CHECK (currency IN ('USD','VES')),
            CONSTRAINT ck_service_prices_created_at_finite CHECK (isfinite(created_at)),
            CONSTRAINT ck_service_prices_updated_at_finite CHECK (
                isfinite(updated_at) AND updated_at >= created_at
            ),
            CONSTRAINT ck_service_prices_version CHECK (version > 0)
        );

        CREATE TABLE nightingale.service_offer_prices (
            account_id uuid NOT NULL,
            professional_id uuid NOT NULL,
            service_id uuid NOT NULL,
            amount numeric(12,2) NOT NULL,
            currency text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            version integer NOT NULL DEFAULT 1,
            PRIMARY KEY (account_id,professional_id,service_id),
            FOREIGN KEY (account_id,professional_id,service_id)
                REFERENCES nightingale.professional_services(account_id,professional_id,service_id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_service_offer_prices_amount CHECK (amount >= 0),
            CONSTRAINT ck_service_offer_prices_currency CHECK (currency IN ('USD','VES')),
            CONSTRAINT ck_service_offer_prices_created_at_finite CHECK (isfinite(created_at)),
            CONSTRAINT ck_service_offer_prices_updated_at_finite CHECK (
                isfinite(updated_at) AND updated_at >= created_at
            ),
            CONSTRAINT ck_service_offer_prices_version CHECK (version > 0)
        );

        CREATE TABLE nightingale.patient_charges (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL,
            patient_id uuid NOT NULL,
            appointment_id uuid,
            encounter_id uuid,
            service_id uuid,
            description text NOT NULL,
            amount numeric(12,2) NOT NULL,
            currency text NOT NULL,
            price_source text NOT NULL,
            status text NOT NULL DEFAULT 'draft',
            issued_at timestamptz,
            cancelled_at timestamptz,
            cancellation_reason text,
            created_by uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            version integer NOT NULL DEFAULT 1,
            CONSTRAINT uq_patient_charges_id_account UNIQUE (id,account_id),
            FOREIGN KEY (account_id,patient_id)
                REFERENCES nightingale.account_patients(account_id,patient_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (account_id,appointment_id,patient_id)
                REFERENCES nightingale.appointments(account_id,id,patient_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (account_id,encounter_id,patient_id)
                REFERENCES nightingale.clinical_encounters(account_id,id,patient_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (created_by) REFERENCES nightingale.app_users(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_patient_charges_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_patient_charges_description CHECK (btrim(description)<>''),
            CONSTRAINT ck_patient_charges_amount CHECK (amount >= 0),
            CONSTRAINT ck_patient_charges_currency CHECK (currency IN ('USD','VES')),
            CONSTRAINT ck_patient_charges_price_source
                CHECK (price_source IN ('offer','base','manual')),
            CONSTRAINT ck_patient_charges_status
                CHECK (status IN ('draft','issued','cancelled')),
            CONSTRAINT ck_patient_charges_issued_at_finite
                CHECK (issued_at IS NULL OR isfinite(issued_at)),
            CONSTRAINT ck_patient_charges_cancelled_at_finite
                CHECK (cancelled_at IS NULL OR isfinite(cancelled_at)),
            CONSTRAINT ck_patient_charges_cancellation_reason
                CHECK (cancellation_reason IS NULL OR btrim(cancellation_reason)<>''),
            CONSTRAINT ck_patient_charges_status_coherence CHECK (
                (status='draft' AND issued_at IS NULL AND cancelled_at IS NULL)
                OR (status='issued' AND issued_at IS NOT NULL AND cancelled_at IS NULL)
                OR (status='cancelled' AND issued_at IS NOT NULL
                    AND cancelled_at IS NOT NULL AND cancellation_reason IS NOT NULL)
            ),
            CONSTRAINT ck_patient_charges_created_at_finite CHECK (isfinite(created_at)),
            CONSTRAINT ck_patient_charges_updated_at_finite CHECK (
                isfinite(updated_at) AND updated_at >= created_at
            ),
            CONSTRAINT ck_patient_charges_version CHECK (version > 0)
        );
        CREATE INDEX ix_patient_charges_patient
            ON nightingale.patient_charges (account_id,patient_id,created_at);
        CREATE INDEX ix_patient_charges_status
            ON nightingale.patient_charges (account_id,status,created_at);

        CREATE TABLE nightingale.charge_histories (
            id uuid PRIMARY KEY,
            charge_id uuid NOT NULL,
            account_id uuid NOT NULL,
            action text NOT NULL,
            charge_version integer NOT NULL,
            actor_id uuid NOT NULL,
            reason text,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (charge_id,account_id)
                REFERENCES nightingale.patient_charges(id,account_id)
                ON DELETE RESTRICT,
            FOREIGN KEY (actor_id) REFERENCES nightingale.app_users(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_charge_histories_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_charge_histories_action CHECK (
                action IN ('created','draft_updated','amount_adjusted','issued',
                           'cancelled','corrected')
            ),
            CONSTRAINT ck_charge_histories_charge_version CHECK (charge_version > 0),
            CONSTRAINT ck_charge_histories_reason
                CHECK (reason IS NULL OR btrim(reason)<>''),
            CONSTRAINT ck_charge_histories_created_at_finite CHECK (isfinite(created_at))
        );
        CREATE INDEX ix_charge_histories_charge
            ON nightingale.charge_histories (charge_id,created_at);
    """

    for statement in statements.split(";"):
        if statement.strip():
            op.execute(statement)

    for table, privileges in GRANTS:
        op.execute(f"GRANT {privileges} ON nightingale.{table} TO nightingale_runtime")


def downgrade():
    for table, privileges in GRANTS:
        op.execute(f"REVOKE {privileges} ON nightingale.{table} FROM nightingale_runtime")

    op.execute("DROP TABLE nightingale.charge_histories")
    op.execute("DROP TABLE nightingale.patient_charges")
    op.execute("DROP TABLE nightingale.service_offer_prices")
    op.execute("DROP TABLE nightingale.service_prices")
