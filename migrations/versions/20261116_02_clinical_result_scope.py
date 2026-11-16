"""Clinical section scope for operation results."""

from alembic import op

revision = "20261116_02"
down_revision = "20261116_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE nightingale.operation_receipts
        ADD COLUMN clinical_section text
        CHECK (clinical_section IN ('profile','conditions','allergies'))
    """)
    op.execute("SET CONSTRAINTS ALL IMMEDIATE")
    op.execute("ALTER TABLE nightingale.operation_receipts DISABLE TRIGGER guard_operation_history")
    op.execute("""
        UPDATE nightingale.operation_receipts
        SET clinical_section = CASE
            WHEN action='SetPatientSexAtBirth' THEN 'profile'
            WHEN action IN ('CreatePatientCondition','UpdatePatientCondition','InvalidatePatientCondition') THEN 'conditions'
            WHEN action IN ('CreatePatientAllergyIntolerance','UpdatePatientAllergyIntolerance','InvalidatePatientAllergyIntolerance') THEN 'allergies'
            WHEN action='SetPatientClinicalSectionReview'
                AND result_json#>>'{state,section}' IN ('conditions','allergies')
                THEN result_json#>>'{state,section}'
        END
        WHERE action IN (
            'SetPatientSexAtBirth',
            'CreatePatientCondition','UpdatePatientCondition','InvalidatePatientCondition',
            'CreatePatientAllergyIntolerance','UpdatePatientAllergyIntolerance','InvalidatePatientAllergyIntolerance',
            'SetPatientClinicalSectionReview'
        )
    """)
    op.execute("SET CONSTRAINTS ALL IMMEDIATE")
    op.execute("ALTER TABLE nightingale.operation_receipts ENABLE TRIGGER guard_operation_history")


def downgrade():
    op.execute("ALTER TABLE nightingale.operation_receipts DROP COLUMN clinical_section")
