"""Timeline entries for stage 3 blocks."""

from alembic import op

revision = "20261117_07"
down_revision = "20261117_06"
branch_labels = None
depends_on = None

ENTRY_TYPES = (
    "'encounter','note','measurement','immunization','antecedent','condition',"
    "'allergy_intolerance','declared_medication','care_plan','diagnostic_report',"
    "'specialty_record'"
)
SECTIONS = (
    "'encounters','notes','measurements','immunizations','antecedents','conditions',"
    "'allergies','declared_medications','care_plans','diagnostic_reports',"
    "'specialty_templates'"
)
PAIRS = """((entry_type='encounter' AND source_section='encounters')
     OR (entry_type='note' AND source_section='notes')
     OR (entry_type='measurement' AND source_section='measurements')
     OR (entry_type='immunization' AND source_section='immunizations')
     OR (entry_type='antecedent' AND source_section='antecedents')
     OR (entry_type='condition' AND source_section='conditions')
     OR (entry_type='allergy_intolerance' AND source_section='allergies')
     OR (entry_type='declared_medication' AND source_section='declared_medications')
     OR (entry_type='care_plan' AND source_section='care_plans')
     OR (entry_type='diagnostic_report' AND source_section='diagnostic_reports')
     OR (entry_type='specialty_record' AND source_section='specialty_templates'))"""
LEGACY_PAIRS = """((entry_type='encounter' AND source_section='encounters')
     OR (entry_type='note' AND source_section='notes')
     OR (entry_type='measurement' AND source_section='measurements')
     OR (entry_type='immunization' AND source_section='immunizations')
     OR (entry_type='antecedent' AND source_section='antecedents')
     OR (entry_type='condition' AND source_section='conditions')
     OR (entry_type='allergy_intolerance' AND source_section='allergies'))"""


def _replace(name: str, expression: str) -> None:
    op.execute(f"ALTER TABLE nightingale.patient_clinical_timeline DROP CONSTRAINT {name}")
    op.execute(
        f"ALTER TABLE nightingale.patient_clinical_timeline "
        f"ADD CONSTRAINT {name} CHECK ({expression})"
    )


def upgrade():
    _replace("patient_clinical_timeline_check1", PAIRS)
    _replace(
        "patient_clinical_timeline_entry_type_check",
        f"entry_type IN ({ENTRY_TYPES})",
    )
    _replace(
        "patient_clinical_timeline_source_section_check",
        f"source_section IN ({SECTIONS})",
    )


def downgrade():
    _replace("patient_clinical_timeline_check1", LEGACY_PAIRS)
    _replace(
        "patient_clinical_timeline_entry_type_check",
        "entry_type IN ('encounter','note','measurement','immunization','antecedent','condition','allergy_intolerance')",
    )
    _replace(
        "patient_clinical_timeline_source_section_check",
        "source_section IN ('encounters','notes','measurements','immunizations','antecedents','conditions','allergies')",
    )
