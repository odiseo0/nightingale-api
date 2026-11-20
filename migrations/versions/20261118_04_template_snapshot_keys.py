"""Allow versioned specialty template keys in materialized snapshots."""

from alembic import op

revision = "20261118_04"
down_revision = "20261118_03"
branch_labels = None
depends_on = None


def _replace(include_templates: bool):
    template_rule = """
        IF value ?& ARRAY['templateId','version']
            AND (SELECT count(*) FROM jsonb_object_keys(value))=2
            AND value->>'templateId' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            AND value->>'version' ~ '^[1-9][0-9]*$' THEN
            RETURN true;
        END IF;""" if include_templates else ""
    op.execute(f"""
        CREATE OR REPLACE FUNCTION nightingale.valid_entity_key(value jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT AS $$
        DECLARE item text;
        BEGIN
            IF jsonb_typeof(value)='string' THEN
                RETURN value #>> '{{}}' ~ '^[0-9a-f]{{8}}-[0-9a-f]{{4}}-7[0-9a-f]{{3}}-[89ab][0-9a-f]{{3}}-[0-9a-f]{{12}}$';
            END IF;{template_rule}
            IF value ?& ARRAY['patientId','section']
                AND (SELECT count(*) FROM jsonb_object_keys(value))=2
                AND value->>'section' IN ('conditions','allergies') THEN
                RETURN value->>'patientId' ~ '^[0-9a-f]{{8}}-[0-9a-f]{{4}}-7[0-9a-f]{{3}}-[89ab][0-9a-f]{{3}}-[0-9a-f]{{12}}$';
            END IF;
            IF jsonb_typeof(value)<>'object' OR NOT (
                (value ?& ARRAY['patientId','contactPersonId'] OR value ?& ARRAY['professionalId','serviceId'])
                AND (SELECT count(*) FROM jsonb_object_keys(value))=2
            ) THEN RETURN false; END IF;
            FOR item IN SELECT v #>> '{{}}' FROM jsonb_each(value) AS pair(k,v) LOOP
                IF item IS NULL OR item !~ '^[0-9a-f]{{8}}-[0-9a-f]{{4}}-7[0-9a-f]{{3}}-[89ab][0-9a-f]{{3}}-[0-9a-f]{{12}}$' THEN
                    RETURN false;
                END IF;
            END LOOP;
            RETURN true;
        END;
        $$
    """)


def upgrade():
    _replace(True)


def downgrade():
    _replace(False)
