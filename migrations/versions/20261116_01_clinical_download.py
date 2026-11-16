"""Clinical section review keys in snapshots and journal."""

from alembic import op

revision = "20261116_01"
down_revision = "20261115_04"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_entity_key(value jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT AS $$
        DECLARE item text;
        BEGIN
            IF jsonb_typeof(value)='string' THEN
                RETURN value #>> '{}' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$';
            END IF;
            IF value ?& ARRAY['patientId','section']
                AND (SELECT count(*) FROM jsonb_object_keys(value))=2
                AND value->>'section' IN ('conditions','allergies') THEN
                RETURN value->>'patientId' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$';
            END IF;
            IF jsonb_typeof(value)<>'object' OR NOT (
                (value ?& ARRAY['patientId','contactPersonId'] OR value ?& ARRAY['professionalId','serviceId'])
                AND (SELECT count(*) FROM jsonb_object_keys(value))=2
            ) THEN RETURN false; END IF;
            FOR item IN SELECT v #>> '{}' FROM jsonb_each(value) AS pair(k,v) LOOP
                IF item IS NULL OR item !~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN
                    RETURN false;
                END IF;
            END LOOP;
            RETURN true;
        END;
        $$
    """)


def downgrade():
    op.execute("""
        CREATE OR REPLACE FUNCTION nightingale.valid_entity_key(value jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT AS $$
        DECLARE item text;
        BEGIN
            IF jsonb_typeof(value)='string' THEN
                RETURN value #>> '{}' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$';
            END IF;
            IF jsonb_typeof(value)<>'object' OR NOT (
                (value ?& ARRAY['patientId','contactPersonId'] OR value ?& ARRAY['professionalId','serviceId'])
                AND (SELECT count(*) FROM jsonb_object_keys(value))=2
            ) THEN RETURN false; END IF;
            FOR item IN SELECT v #>> '{}' FROM jsonb_each(value) AS pair(k,v) LOOP
                IF item IS NULL OR item !~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN
                    RETURN false;
                END IF;
            END LOOP;
            RETURN true;
        END;
        $$
    """)
