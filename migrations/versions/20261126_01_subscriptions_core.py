"""Add the subscriptions commercial core: plans, versions, subscriptions and periods."""

from alembic import op


revision = "20261126_01"
down_revision = "20261122_01"
branch_labels = None
depends_on = None

GRANTS = (
    ("subscription_plans", "SELECT,INSERT,UPDATE"),
    ("subscription_plan_versions", "SELECT,INSERT"),
    ("account_subscriptions", "SELECT,INSERT,UPDATE"),
    ("subscription_periods", "SELECT,INSERT"),
)


def upgrade():
    statements = """
        CREATE TABLE nightingale.subscription_plans (
            id uuid PRIMARY KEY,
            code text NOT NULL UNIQUE,
            name text NOT NULL,
            description text NOT NULL,
            status text NOT NULL DEFAULT 'available',
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            version integer NOT NULL DEFAULT 1,
            CONSTRAINT ck_subscription_plans_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_subscription_plans_code
                CHECK (code IN ('independent','small_practice','medical_center')),
            CONSTRAINT ck_subscription_plans_name CHECK (btrim(name)<>''),
            CONSTRAINT ck_subscription_plans_description CHECK (btrim(description)<>''),
            CONSTRAINT ck_subscription_plans_status
                CHECK (status IN ('available','retired')),
            CONSTRAINT ck_subscription_plans_created_at_finite CHECK (isfinite(created_at)),
            CONSTRAINT ck_subscription_plans_updated_at_finite CHECK (
                isfinite(updated_at) AND updated_at >= created_at
            ),
            CONSTRAINT ck_subscription_plans_version CHECK (version > 0)
        );

        CREATE TABLE nightingale.subscription_plan_versions (
            id uuid PRIMARY KEY,
            plan_id uuid NOT NULL,
            version integer NOT NULL,
            seat_limit integer NOT NULL,
            price_30d_usd numeric(12,2) NOT NULL,
            price_year_usd numeric(12,2) NOT NULL,
            currency text NOT NULL DEFAULT 'USD',
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (plan_id,version),
            FOREIGN KEY (plan_id) REFERENCES nightingale.subscription_plans(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_subscription_plan_versions_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_subscription_plan_versions_version CHECK (version > 0),
            CONSTRAINT ck_subscription_plan_versions_seat_limit CHECK (seat_limit > 0),
            CONSTRAINT ck_subscription_plan_versions_price_30d
                CHECK (price_30d_usd > 0),
            CONSTRAINT ck_subscription_plan_versions_price_year
                CHECK (price_year_usd > 0),
            CONSTRAINT ck_subscription_plan_versions_currency CHECK (currency='USD'),
            CONSTRAINT ck_subscription_plan_versions_created_at_finite
                CHECK (isfinite(created_at))
        );

        CREATE TABLE nightingale.account_subscriptions (
            id uuid PRIMARY KEY,
            account_id uuid NOT NULL UNIQUE,
            plan_version_id uuid NOT NULL,
            status text NOT NULL DEFAULT 'pending_activation',
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            version integer NOT NULL DEFAULT 1,
            FOREIGN KEY (account_id) REFERENCES nightingale.accounts(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (plan_version_id)
                REFERENCES nightingale.subscription_plan_versions(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_account_subscriptions_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_account_subscriptions_status CHECK (
                status IN ('pending_activation','active','grace','suspended','cancelled')
            ),
            CONSTRAINT ck_account_subscriptions_created_at_finite
                CHECK (isfinite(created_at)),
            CONSTRAINT ck_account_subscriptions_updated_at_finite CHECK (
                isfinite(updated_at) AND updated_at >= created_at
            ),
            CONSTRAINT ck_account_subscriptions_version CHECK (version > 0)
        );

        CREATE TABLE nightingale.subscription_periods (
            id uuid PRIMARY KEY,
            subscription_id uuid NOT NULL,
            plan_version_id uuid NOT NULL,
            periodicity text NOT NULL,
            starts_at timestamptz NOT NULL,
            ends_at timestamptz NOT NULL,
            sequence integer NOT NULL,
            created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (subscription_id,sequence),
            FOREIGN KEY (subscription_id) REFERENCES nightingale.account_subscriptions(id)
                ON DELETE RESTRICT,
            FOREIGN KEY (plan_version_id)
                REFERENCES nightingale.subscription_plan_versions(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_subscription_periods_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_subscription_periods_periodicity
                CHECK (periodicity IN ('days_30','year_1')),
            CONSTRAINT ck_subscription_periods_starts_at_finite CHECK (isfinite(starts_at)),
            CONSTRAINT ck_subscription_periods_ends_at_finite CHECK (
                isfinite(ends_at) AND ends_at > starts_at
            ),
            CONSTRAINT ck_subscription_periods_sequence CHECK (sequence > 0),
            CONSTRAINT ex_subscription_periods_overlap EXCLUDE USING gist (
                subscription_id WITH =,
                tstzrange(starts_at, ends_at) WITH &&
            )
        );
    """

    for statement in statements.split(";"):
        if statement.strip():
            op.execute(statement)

    # Initial catalog decided in D21 (2026-11-26): version 1 of each plan.
    op.execute("""
        INSERT INTO nightingale.subscription_plans (id,code,name,description) VALUES
            ('019c1000-0000-7000-8000-000000000001','independent',
             'Médico independiente','Plan para un médico independiente'),
            ('019c1000-0000-7000-8000-000000000002','small_practice',
             'Consultorio pequeño','Plan para un consultorio pequeño'),
            ('019c1000-0000-7000-8000-000000000003','medical_center',
             'Centro médico','Plan para un centro médico')
    """)
    op.execute("""
        INSERT INTO nightingale.subscription_plan_versions
            (id,plan_id,version,seat_limit,price_30d_usd,price_year_usd) VALUES
            ('019c1000-0000-7000-8000-000000000011',
             '019c1000-0000-7000-8000-000000000001',1,2,18.00,100.00),
            ('019c1000-0000-7000-8000-000000000012',
             '019c1000-0000-7000-8000-000000000002',1,5,24.00,240.00),
            ('019c1000-0000-7000-8000-000000000013',
             '019c1000-0000-7000-8000-000000000003',1,20,75.00,500.00)
    """)

    for table, privileges in GRANTS:
        op.execute(f"GRANT {privileges} ON nightingale.{table} TO nightingale_runtime")


def downgrade():
    for table, privileges in GRANTS:
        op.execute(f"REVOKE {privileges} ON nightingale.{table} FROM nightingale_runtime")

    op.execute("DROP TABLE nightingale.subscription_periods")
    op.execute("DROP TABLE nightingale.account_subscriptions")
    op.execute("DROP TABLE nightingale.subscription_plan_versions")
    op.execute("DROP TABLE nightingale.subscription_plans")
