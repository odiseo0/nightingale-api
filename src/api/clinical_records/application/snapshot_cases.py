from __future__ import annotations

from typing import TYPE_CHECKING

from src.api.accounts.domain.accounts import AccountContext, ClinicalSection
from src.api.clinical_records.application.allergies_cases import (
    allergy_response,
    allergy_review_response,
)
from src.api.clinical_records.application.antecedents_cases import antecedent_response
from src.api.clinical_records.application.clinical_cases import (
    clinical_profile_response,
)
from src.api.clinical_records.application.conditions_cases import (
    condition_response,
    condition_review_response,
)
from src.api.clinical_records.application.immunizations_cases import (
    immunization_response,
)
from src.api.clinical_records.application.measurements_cases import measurement_response
from src.api.clinical_records.application.notes_cases import note_response
from src.api.clinical_records.repository.dao import (
    dao_allergies,
    dao_antecedents,
    dao_clinical_profiles,
    dao_conditions,
    dao_immunizations,
    dao_measurements,
    dao_notes,
    dao_section_reviews,
)
from src.api.patients.application.patients_cases import clinical_patient, clinical_today
from src.api.sync.domain.downloads import SyncItem
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_clinical(
    db: AsyncSession, context: AccountContext, sections: list[ClinicalSection]
) -> list[SyncItem]:
    items: list[SyncItem] = []
    account_id = context.account.id
    today = await clinical_today(db, context.account.time_zone)

    if "profile" in sections:
        profiles, _ = await dao_clinical_profiles.get_multi(
            db,
            where={"account_id": account_id},
            ordering=[("patient_id", False)],
            shows=None,
        )

        for profile in profiles:
            patient = await clinical_patient(db, account_id, profile.patient_id)

            if patient is not Empty:
                items.append(
                    SyncItem(
                        entity_type="patient_clinical_profile",
                        entity_key=profile.patient_id,
                        entity_version=profile.version,
                        state=clinical_profile_response(profile, patient, today),
                    )
                )

    if "conditions" in sections:
        conditions, _ = await dao_conditions.get_multi(
            db,
            where={"account_id": account_id},
            ordering=[("patient_id", False), ("id", False)],
            shows=None,
        )
        items.extend(
            SyncItem(
                entity_type="patient_condition",
                entity_key=condition.id,
                entity_version=condition.version,
                state=condition_response(condition),
            )
            for condition in conditions
        )
        reviews, _ = await dao_section_reviews.get_multi(
            db,
            where={"account_id": account_id, "section": "conditions"},
            ordering=[("patient_id", False)],
            shows=None,
        )

        for review in reviews:
            items.append(
                SyncItem(
                    entity_type="patient_clinical_section_review",
                    entity_key={
                        "patientId": review.patient_id,
                        "section": "conditions",
                    },
                    entity_version=review.version,
                    state=await condition_review_response(
                        db, context, review.patient_id
                    ),
                )
            )

    if "allergies" in sections:
        allergies, _ = await dao_allergies.get_multi(
            db,
            where={"account_id": account_id},
            ordering=[("patient_id", False), ("id", False)],
            shows=None,
        )
        items.extend(
            SyncItem(
                entity_type="patient_allergy_intolerance",
                entity_key=allergy.id,
                entity_version=allergy.version,
                state=allergy_response(allergy),
            )
            for allergy in allergies
        )
        reviews, _ = await dao_section_reviews.get_multi(
            db,
            where={"account_id": account_id, "section": "allergies"},
            ordering=[("patient_id", False)],
            shows=None,
        )

        for review in reviews:
            items.append(
                SyncItem(
                    entity_type="patient_clinical_section_review",
                    entity_key={"patientId": review.patient_id, "section": "allergies"},
                    entity_version=review.version,
                    state=await allergy_review_response(db, context, review.patient_id),
                )
            )

    if "antecedents" in sections:
        items.extend(
            SyncItem(
                entity_type="patient_antecedent",
                entity_key=antecedent.id,
                entity_version=antecedent.version,
                state=antecedent_response(antecedent),
            )
            for antecedent in await dao_antecedents.valid_snapshot(db, account_id)
        )

    if "immunizations" in sections:
        items.extend(
            SyncItem(
                entity_type="patient_immunization",
                entity_key=immunization.id,
                entity_version=immunization.version,
                state=immunization_response(immunization),
            )
            for immunization in await dao_immunizations.valid_snapshot(db, account_id)
        )

    if "measurements" in sections:
        for measurement in await dao_measurements.valid_snapshot(db, account_id):
            items.append(
                SyncItem(
                    entity_type="patient_measurement",
                    entity_key=measurement.id,
                    entity_version=measurement.version,
                    state=await measurement_response(db, context, measurement),
                )
            )

    if "notes" in sections:
        items.extend(
            SyncItem(
                entity_type="patient_note",
                entity_key=note.id,
                entity_version=note.version,
                state=note_response(note),
            )
            for note in await dao_notes.valid_snapshot(db, account_id)
        )

    return items
