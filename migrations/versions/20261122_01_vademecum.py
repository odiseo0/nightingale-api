"""Add the global read-only vademecum catalog."""

from alembic import op


revision = "20261122_01"
down_revision = "20261120_01"
branch_labels = None
depends_on = None

TABLES = (
    "vademecum_datasets",
    "vademecum_products",
    "vademecum_product_ingredients",
    "vademecum_monographs",
    "vademecum_product_monographs",
)


def upgrade():
    statements = """
        CREATE TABLE nightingale.vademecum_datasets (
            id uuid PRIMARY KEY,
            source_sha256 text NOT NULL UNIQUE,
            schema_version text NOT NULL,
            registry_cutoff_date date NOT NULL,
            medical_notice text NOT NULL,
            imported_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            active boolean NOT NULL DEFAULT false,
            CONSTRAINT ck_vademecum_datasets_uuidv7 CHECK (
                substring(id::text from 15 for 1)='7'
                AND substring(id::text from 20 for 1) IN ('8','9','a','b')
            ),
            CONSTRAINT ck_vademecum_datasets_source_sha256
                CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_vademecum_datasets_schema_version
                CHECK (schema_version='1.0.0'),
            CONSTRAINT ck_vademecum_datasets_cutoff_finite
                CHECK (isfinite(registry_cutoff_date)),
            CONSTRAINT ck_vademecum_datasets_medical_notice
                CHECK (btrim(medical_notice)<>''),
            CONSTRAINT ck_vademecum_datasets_imported_at_finite
                CHECK (isfinite(imported_at))
        );
        CREATE UNIQUE INDEX uq_vademecum_datasets_active
            ON nightingale.vademecum_datasets (active) WHERE active;

        CREATE TABLE nightingale.vademecum_products (
            dataset_id uuid NOT NULL,
            registration_number text NOT NULL,
            name text NOT NULL,
            active_ingredient_text text NOT NULL,
            approved_at timestamptz NOT NULL,
            valid_until timestamptz NOT NULL,
            representative text NOT NULL,
            manufacturer text,
            ingredient_link_status text NOT NULL,
            ingredient_resolution text NOT NULL,
            product_reference jsonb,
            search_text text NOT NULL,
            PRIMARY KEY (dataset_id,registration_number),
            FOREIGN KEY (dataset_id) REFERENCES nightingale.vademecum_datasets(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_vademecum_products_registration_number
                CHECK (btrim(registration_number)<>''),
            CONSTRAINT ck_vademecum_products_name CHECK (btrim(name)<>''),
            CONSTRAINT ck_vademecum_products_approved_at_finite
                CHECK (isfinite(approved_at)),
            CONSTRAINT ck_vademecum_products_valid_until_finite
                CHECK (isfinite(valid_until)),
            CONSTRAINT ck_vademecum_products_representative
                CHECK (btrim(representative)<>''),
            CONSTRAINT ck_vademecum_products_manufacturer
                CHECK (manufacturer IS NULL OR btrim(manufacturer)<>''),
            CONSTRAINT ck_vademecum_products_ingredient_link_status CHECK (
                ingredient_link_status IN ('complete','unlinked','missing_ingredient',
                'historical_complete','product_reference','inferred_complete',
                'combination_only','historical_partial','inferred_partial','partial')
            ),
            CONSTRAINT ck_vademecum_products_ingredient_resolution CHECK (
                ingredient_resolution IN ('source_text','historical_product_match',
                'unresolved','product_name_inference','product_reference')
            ),
            CONSTRAINT ck_vademecum_products_product_reference_object CHECK (
                product_reference IS NULL OR jsonb_typeof(product_reference)='object'
            )
        );
        CREATE INDEX ix_vademecum_products_order
            ON nightingale.vademecum_products (dataset_id,name,registration_number);

        CREATE TABLE nightingale.vademecum_monographs (
            dataset_id uuid NOT NULL,
            id text NOT NULL,
            name text NOT NULL,
            atc_code text NOT NULL,
            document jsonb NOT NULL,
            search_text text NOT NULL,
            PRIMARY KEY (dataset_id,id),
            FOREIGN KEY (dataset_id) REFERENCES nightingale.vademecum_datasets(id)
                ON DELETE RESTRICT,
            CONSTRAINT ck_vademecum_monographs_monograph_id
                CHECK (id ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
            CONSTRAINT ck_vademecum_monographs_name CHECK (btrim(name)<>''),
            CONSTRAINT ck_vademecum_monographs_document_object
                CHECK (jsonb_typeof(document)='object')
        );
        CREATE INDEX ix_vademecum_monographs_order
            ON nightingale.vademecum_monographs (dataset_id,name,id);

        CREATE TABLE nightingale.vademecum_product_ingredients (
            dataset_id uuid NOT NULL,
            registration_number text NOT NULL,
            ingredient_id text NOT NULL,
            PRIMARY KEY (dataset_id,registration_number,ingredient_id),
            FOREIGN KEY (dataset_id,registration_number)
                REFERENCES nightingale.vademecum_products(dataset_id,registration_number)
                ON DELETE RESTRICT,
            CONSTRAINT ck_vademecum_product_ingredients_ingredient_id
                CHECK (btrim(ingredient_id)<>'')
        );
        CREATE INDEX ix_vademecum_product_ingredients_inverse
            ON nightingale.vademecum_product_ingredients
            (dataset_id,ingredient_id,registration_number);

        CREATE TABLE nightingale.vademecum_product_monographs (
            dataset_id uuid NOT NULL,
            registration_number text NOT NULL,
            monograph_id text NOT NULL,
            combination boolean NOT NULL,
            PRIMARY KEY (dataset_id,registration_number,monograph_id),
            FOREIGN KEY (dataset_id,registration_number)
                REFERENCES nightingale.vademecum_products(dataset_id,registration_number)
                ON DELETE RESTRICT,
            FOREIGN KEY (dataset_id,monograph_id)
                REFERENCES nightingale.vademecum_monographs(dataset_id,id)
                ON DELETE RESTRICT
        );
        CREATE INDEX ix_vademecum_product_monographs_inverse
            ON nightingale.vademecum_product_monographs
            (dataset_id,monograph_id,registration_number)
    """.split(";")
    for statement in statements:
        if statement.strip():
            op.execute(statement)

    for table in TABLES:
        op.execute(f"GRANT SELECT ON nightingale.{table} TO nightingale_runtime")


def downgrade():
    for table in TABLES:
        op.execute(f"REVOKE SELECT ON nightingale.{table} FROM nightingale_runtime")
    for table in reversed(TABLES):
        op.execute(f"DROP TABLE nightingale.{table}")
