from __future__ import annotations

import json
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from pydantic import ValidationError

from src.api.accounts.application.accounts_cases import readable_clinical_sections
from src.api.accounts.application.snapshot_cases import snapshot_accounts
from src.api.accounts.domain.accounts import AccountContext, ProfessionalResponse
from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.accounts.domain.policies import projection_allowed, sync_scope_matches
from src.api.subscriptions.application.projection_cases import snapshot_subscription
from src.api.appointments.application.snapshot_cases import snapshot_appointments
from src.api.appointments.domain.appointments import (
    AppointmentHistoryProjection,
    AppointmentResponse,
)
from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.application.snapshot_cases import snapshot_clinical
from src.api.clinical_records.domain.allergies import PatientAllergyIntoleranceResponse
from src.api.clinical_records.domain.antecedents import PatientAntecedentResponse
from src.api.clinical_records.domain.clinical import ClinicalProfileResponse
from src.api.clinical_records.domain.conditions import (
    ClinicalSectionReviewResponse,
    PatientConditionResponse,
)
from src.api.clinical_records.domain.immunizations import PatientImmunizationResponse
from src.api.care_plans.domain.goals import (
    CarePlanActionResponse,
    CarePlanGoalResponse,
    CarePlanReviewResponse,
)
from src.api.care_plans.domain.plans import CarePlanResponse
from src.api.diagnostic_results.domain.reports import DiagnosticReportResponse
from src.api.diagnostic_results.domain.results import (
    DiagnosticReportResultResponse,
    ReportAttachmentResponse,
)
from src.api.specialties.domain.odontogram import (
    DentalFindingResponse,
    DentalTreatmentResponse,
)
from src.api.specialties.domain.records import SpecialtyRecordResponse
from src.api.specialties.domain.templates import SpecialtyTemplateResponse
from src.api.medications.domain.medications import DeclaredMedicationResponse
from src.api.clinical_records.domain.measurements import PatientMeasurementResponse
from src.api.clinical_records.domain.notes import PatientNoteResponse
from src.api.encounters.application.snapshot_cases import snapshot_encounters
from src.api.care_plans.application.snapshot_cases import snapshot_care_plans
from src.api.diagnostic_results.application.snapshot_cases import (
    snapshot_diagnostic_reports,
)
from src.api.specialties.application.snapshot_cases import (
    snapshot_specialty_templates,
)
from src.api.medications.application.snapshot_cases import (
    snapshot_declared_medications,
)
from src.api.encounters.domain.encounters import PatientEncounterResponse
from src.api.patients.application.snapshot_cases import snapshot_patients
from src.api.schedule.application.snapshot_cases import snapshot_schedule
from src.api.services.application.snapshot_cases import snapshot_services
from src.api.sync.application.operations_cases import authorized_context
from src.api.sync.domain.downloads import (
    SnapshotRequest,
    SnapshotResponse,
    SyncItem,
    SyncPosition,
    SyncWindow,
)
from src.api.sync.domain.errors import SyncReadError
from src.api.sync.repository.dao import dao_heads, dao_snapshot_items, dao_snapshots
from src.core import Err, Ok, Result
from src.core.db import DAOError, transaction
from src.core.schema import PageQuery, PaginatedResponse
from src.core.services.sync_signatures import sign_position
from src.core.utils.utils import Empty
from src.settings.api_settings import api_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.sync.repository.models import SyncSnapshot

type SnapshotError = (
    InvalidCredential
    | AccessDenied
    | AccountNotFound
    | AccountObjectNotFound
    | SyncReadError
)


def snapshot_response(row: SyncSnapshot) -> Result[SnapshotResponse, SyncReadError]:
    secret = api_settings.sync_signing_key

    if secret is None:
        return Err(SyncReadError("DEPENDENCY_UNAVAILABLE"))

    window = SyncWindow(
        appointments_from=row.appointments_from,
        appointments_until=row.appointments_until,
        time_zone=row.window_time_zone,
        starts_at=row.window_starts_at,
        ends_at=row.window_ends_at,
    )
    position = SyncPosition(
        account_id=row.account_id,
        user_id=row.user_id,
        device_id=row.device_id,
        audience=row.audience,
        permission_epoch=row.permission_epoch,
        sequence=row.base_sequence,
        window=window,
        clinical_sections=row.clinical_sections,
        issued_at=row.date_added,
        expires_at=row.date_added + timedelta(days=90),
    )
    cursor = sign_position(
        position.model_dump_json(by_alias=True).encode(),
        secret.get_secret_value().encode(),
    )

    return Ok(
        SnapshotResponse(
            snapshot_id=row.id,
            account_id=row.account_id,
            model_revision=row.model_revision,
            window=window,
            base_cursor=cursor,
            expires_at=row.expires_at,
            item_count=row.item_count,
            clinical_sections=row.clinical_sections,
        )
    )


async def create_snapshot(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    request: SnapshotRequest,
) -> Result[SnapshotResponse, SnapshotError]:
    async with transaction(db, isolation_level="REPEATABLE READ"):
        scope = await authorized_context(db, credential, account_id)

        if isinstance(scope, Err):
            return scope

        context, head = scope.value

        if api_settings.sync_signing_key is None:
            return Err(SyncReadError("DEPENDENCY_UNAVAILABLE"))

        now = await dao_heads.get_server_time(db)
        today = await dao_heads.local_date(db, context.account.time_zone, now)
        start = request.appointments_from or today - timedelta(days=30)
        end = request.appointments_until or today + timedelta(days=181)
        starts_at, ends_at = await dao_heads.window_bounds(
            db, start, end, context.account.time_zone
        )

        try:
            window = SyncWindow(
                appointments_from=start,
                appointments_until=end,
                time_zone=context.account.time_zone,
                starts_at=starts_at,
                ends_at=ends_at,
            )
        except ValidationError:
            return Err(SyncReadError("VALIDATION_ERROR"))

        clinical_sections = (
            readable_clinical_sections(context) if request.include_clinical else []
        )
        items = await snapshot_accounts(db, context)
        items.extend(await snapshot_subscription(db, context))
        appointments = await snapshot_appointments(db, context, window)
        clinical_items = await snapshot_clinical(db, context, clinical_sections)

        if "encounters" in clinical_sections:
            clinical_items.extend(await snapshot_encounters(db, account_id))

        if "declared_medications" in clinical_sections:
            clinical_items.extend(await snapshot_declared_medications(db, context))

        if "care_plans" in clinical_sections:
            clinical_items.extend(await snapshot_care_plans(db, context))

        if "diagnostic_reports" in clinical_sections:
            clinical_items.extend(await snapshot_diagnostic_reports(db, context))

        if "specialty_templates" in clinical_sections:
            clinical_items.extend(await snapshot_specialty_templates(db, context))

        states = [
            item.state
            for item in appointments
            if isinstance(item.state, AppointmentResponse)
        ]
        histories = [
            entry
            for item in appointments
            if isinstance(item.state, AppointmentHistoryProjection)
            for entry in item.state.items
        ]
        required_contacts = {
            state.responsible_contact_id
            for state in [*states, *histories]
            if state.responsible_contact_id is not None
        }
        required_patients = {state.patient_id for state in states} | {
            item.state.patient_id
            for item in clinical_items
            if isinstance(
                item.state,
                ClinicalProfileResponse
                | PatientConditionResponse
                | ClinicalSectionReviewResponse
                | PatientAllergyIntoleranceResponse
                | PatientEncounterResponse
                | PatientNoteResponse
                | PatientMeasurementResponse
                | PatientImmunizationResponse
                | PatientAntecedentResponse
                | DeclaredMedicationResponse
                | CarePlanResponse
                | CarePlanGoalResponse
                | CarePlanActionResponse
                | CarePlanReviewResponse
                | DiagnosticReportResponse
                | DiagnosticReportResultResponse
                | ReportAttachmentResponse
                | SpecialtyRecordResponse
                | DentalFindingResponse
                | DentalTreatmentResponse,
            )
        }
        items.extend(
            await snapshot_patients(db, context, required_patients, required_contacts)
        )
        professionals = [
            item.state for item in items if isinstance(item.state, ProfessionalResponse)
        ]
        items.extend(
            await snapshot_services(
                db, context, professionals, {state.service_id for state in states}
            )
        )
        items.extend(await snapshot_schedule(db, context, window))
        items.extend(appointments)
        items.extend(clinical_items)
        items = [
            item for item in items
            if projection_allowed(
                item.entity_type, None, context.owner, clinical_sections,
                item.state.section if isinstance(item.state, ClinicalSectionReviewResponse) else None,
            )
        ]
        items.sort(
            key=lambda item: (
                item.entity_type,
                json.dumps(item.model_dump(mode="json")["entity_key"], sort_keys=True),
            )
        )
        snapshot_id = uuid7()
        row = await dao_snapshots.create(
            db,
            commit=False,
            obj_in={
                "id": snapshot_id,
                "account_id": account_id,
                "user_id": context.actor.user_id,
                "device_id": context.actor.device_id,
                "contract_version": 1,
                "model_revision": "api-v1.3",
                "appointments_from": start,
                "appointments_until": end,
                "window_time_zone": window.time_zone,
                "window_starts_at": window.starts_at,
                "window_ends_at": window.ends_at,
                "base_sequence": head.last_sequence,
                "permission_epoch": head.permission_epoch,
                "audience": "owner" if context.owner else "members",
                "item_count": len(items),
                "clinical_sections": clinical_sections,
                "date_added": now,
                "expires_at": now + timedelta(minutes=15),
            },
        )

        for ordinal, item in enumerate(items, 1):
            value = item.model_dump(mode="json", by_alias=True)
            await dao_snapshot_items.record(
                db,
                commit=False,
                values={
                    "snapshot_id": snapshot_id,
                    "ordinal": ordinal,
                    "entity_type": item.entity_type,
                    "entity_key": value["entityKey"],
                    "entity_version": item.entity_version,
                    "state_json": value["state"],
                },
            )

        if clinical_sections:
            await record_control(
                db,
                ControlAudit(
                    account_id=account_id,
                    actor_user_id=context.actor.user_id,
                    actor_device_id=context.actor.device_id,
                    action="CaptureClinicalSnapshot",
                    object_type="sync_snapshot",
                    object_key=str(snapshot_id),
                    outcome="accepted",
                    correlation_id=uuid7(),
                    occurred_at=now,
                ),
            )

        response = snapshot_response(row)

    return response


async def snapshot_context(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    snapshot_id: UUID,
    *,
    release: bool = False,
) -> Result[tuple[AccountContext, SyncSnapshot], SnapshotError]:
    """The caller owns authorization locks and the short read/release transaction."""
    scope = await authorized_context(db, credential, account_id)

    if isinstance(scope, Err):
        return scope

    context, head = scope.value
    row = await dao_snapshots.get(db, snapshot_id)

    if row is Empty:
        return Err(AccountObjectNotFound())

    if (
        row.account_id != account_id
        or row.user_id != context.actor.user_id
        or row.device_id != context.actor.device_id
    ):
        return Err(AccountObjectNotFound())

    if not release:
        if (
            not sync_scope_matches(
                context, row.audience, row.clinical_sections,
                row.permission_epoch, head.permission_epoch,
            )
        ):
            return Err(SyncReadError("SNAPSHOT_SCOPE_CHANGED"))

        if row.expires_at <= await dao_heads.get_server_time(db):
            return Err(SyncReadError("SNAPSHOT_EXPIRED"))

    return Ok((context, row))


async def get_snapshot(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    snapshot_id: UUID,
) -> Result[SnapshotResponse, SnapshotError]:
    async with transaction(db):
        scope = await snapshot_context(db, credential, account_id, snapshot_id)

        if isinstance(scope, Err):
            return scope

        response = snapshot_response(scope.value[1])

    return response


async def snapshot_page(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    snapshot_id: UUID,
    query: PageQuery,
) -> Result[PaginatedResponse[SyncItem], SnapshotError]:
    async with transaction(db):
        scope = await snapshot_context(db, credential, account_id, snapshot_id)

        if isinstance(scope, Err):
            return scope

        row = scope.value[1]
        rows = await dao_snapshot_items.page(
            db, row.id, (query.page - 1) * query.shows, query.shows
        )

        try:
            response = PaginatedResponse[SyncItem](
                total=row.item_count,
                items=[
                    SyncItem.model_validate(
                        {
                            "entity_type": item.entity_type,
                            "entity_key": item.entity_key,
                            "entity_version": item.entity_version,
                            "state": item.state_json,
                        }
                    )
                    for item in rows
                ],
            )
        except ValidationError as error:
            raise DAOError("La captura no cumple su esquema") from error

        if row.clinical_sections:
            await record_control(
                db,
                ControlAudit(
                    account_id=account_id,
                    actor_user_id=scope.value[0].actor.user_id,
                    actor_device_id=scope.value[0].actor.device_id,
                    action="ReadClinicalSnapshotPage",
                    object_type="sync_snapshot",
                    object_key=str(snapshot_id),
                    outcome="accepted",
                    correlation_id=uuid7(),
                    occurred_at=await dao_heads.get_server_time(db),
                ),
            )

    return Ok(response)


async def release_snapshot(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    snapshot_id: UUID,
) -> Result[None, SnapshotError]:
    async with transaction(db):
        scope = await snapshot_context(
            db, credential, account_id, snapshot_id, release=True
        )

        if isinstance(scope, Err):
            return scope

        await dao_snapshots.release(db, snapshot_id)

    return Ok(None)
