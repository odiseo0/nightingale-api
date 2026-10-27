from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import ValidationError

from src.api.accounts.application.accounts_cases import account_context
from src.api.accounts.application.management_cases import account_professional
from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
)
from src.api.accounts.domain.errors import (
    AccountNotFound,
    AccountObjectNotFound,
    AccountRuleError,
)
from src.api.appointments.domain.appointments import (
    AppointmentHistoryProjection,
    AppointmentHistoryQuery,
    AppointmentHistoryResponse,
    AppointmentInterval,
    AppointmentQuery,
    AppointmentReasonPayload,
    AppointmentResponse,
    AppointmentState,
    CreateAppointmentPayload,
    EmptyAppointmentPayload,
)
from src.api.appointments.repository.dao import dao_appointments, dao_histories
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.patients.application.contacts_cases import booking_responsible
from src.api.patients.application.patients_cases import booking_patient
from src.api.schedule.application.availability_cases import available_schedule
from src.api.schedule.domain.schedule import AbsoluteInterval, AvailabilityQuery
from src.api.services.application.offers_cases import booking_service
from src.core import Err, Ok, Result
from src.core.db import DAOError, transaction
from src.core.schema import BaseModel
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.appointments.repository.models import Appointment, AppointmentHistory


async def occupancy(
    db: AsyncSession,
    professional_id: UUID,
    start: datetime,
    end: datetime,
    excluding: UUID | None = None,
) -> tuple[AbsoluteInterval, ...]:
    rows = await dao_appointments.occupancy(db, professional_id, start, end, excluding)

    return tuple(
        AbsoluteInterval(starts_at=row.starts_at, ends_at=row.ends_at) for row in rows
    )


async def apply_appointment_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID | dict[str, UUID],
    expected_version: int,
    payload: BaseModel | None,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    """The caller locks the professional before the account control."""
    if not isinstance(entity_key, UUID):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if action in (
        "ConfirmAppointment",
        "RescheduleAppointment",
        "CancelAppointment",
        "CompleteAppointment",
        "MarkAppointmentNoShow",
    ):
        if not (
            action == "ConfirmAppointment"
            and isinstance(payload, EmptyAppointmentPayload)
            or action == "RescheduleAppointment"
            and isinstance(payload, AppointmentInterval)
            or action
            in ("CancelAppointment", "CompleteAppointment", "MarkAppointmentNoShow")
            and isinstance(payload, AppointmentReasonPayload)
        ):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        row = await dao_appointments.get_by(
            db,
            where={"id": entity_key, "account_id": context.account.id},
            execution_options={"populate_existing": True},
        )

        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        if (
            row.status not in ("scheduled", "confirmed")
            or action == "ConfirmAppointment"
            and row.status != "scheduled"
        ):
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        changes: dict[str, object]

        if isinstance(payload, AppointmentInterval):
            if payload.ends_at - payload.starts_at != row.ends_at - row.starts_at:
                return Err(AccountRuleError("VALIDATION_ERROR", row.version))

            if payload.starts_at == row.starts_at and payload.ends_at == row.ends_at:
                return Err(AccountRuleError("NO_CHANGES", row.version))

            patient = await booking_patient(
                db, context, row.patient_id, payload.starts_at
            )

            if isinstance(patient, Err):
                return patient

            responsible = await booking_responsible(
                db,
                context,
                row.patient_id,
                row.responsible_contact_id,
                payload.starts_at,
                required=patient.value.identification_basis == "minor_without_document",
            )

            if isinstance(responsible, Err):
                return responsible

            service = await booking_service(
                db, context, row.professional_id, row.service_id
            )

            if isinstance(service, Err):
                return service

            busy = await occupancy(
                db, row.professional_id, payload.starts_at, payload.ends_at, row.id
            )
            duration = int((payload.ends_at - payload.starts_at).total_seconds() // 60)
            available = await available_schedule(
                db,
                context,
                row.professional_id,
                payload.starts_at,
                payload.ends_at,
                duration,
                occupied=busy,
            )

            if isinstance(available, Err):
                return available

            if not available.value:
                return Err(AccountRuleError("SLOT_UNAVAILABLE", row.version))

            changes = {
                "starts_at": payload.starts_at,
                "ends_at": payload.ends_at,
                "status": "scheduled",
                "confirmed_at": None,
            }
            history_action = "rescheduled"
        elif isinstance(payload, AppointmentReasonPayload):
            history_action = {
                "CancelAppointment": "cancelled",
                "CompleteAppointment": "completed",
                "MarkAppointmentNoShow": "no_show",
            }[action]
            changes = {"status": history_action}
        else:
            changes = {"status": "confirmed"}
            history_action = "confirmed"

        now = await dao_appointments.server_time(db)

        if (
            action == "CompleteAppointment"
            and now < row.starts_at
            or (
                action == "MarkAppointmentNoShow"
                and now
                < row.starts_at
                + timedelta(minutes=context.account.no_show_grace_minutes)
            )
        ):
            return Err(AccountRuleError("INVALID_STATE_TRANSITION", row.version))

        if action == "ConfirmAppointment":
            changes["confirmed_at"] = now

        previous_starts_at, previous_ends_at = row.starts_at, row.ends_at
        row = await dao_appointments.revise(db, row, changes, now)
        state = AppointmentResponse.model_validate(appointment_response(row))
        reason = (
            payload.change_reason
            if isinstance(payload, AppointmentReasonPayload)
            else None
        )
        await record_history(db, context, state, history_action, now, reason)

        return Ok(
            AccountEffect(
                state,
                state.version,
                [
                    AccountChange(
                        "appointment",
                        str(entity_key),
                        state,
                        state.version,
                        "members",
                        previous_starts_at=previous_starts_at,
                        previous_ends_at=previous_ends_at,
                    )
                ],
                False,
            )
        )

    if action != "CreateAppointment" or not isinstance(
        payload, CreateAppointmentPayload
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    existing = await dao_appointments.get(
        db, entity_key, execution_options={"populate_existing": True}
    )

    if existing is not Empty:
        if existing.account_id != context.account.id:
            return Err(AccountObjectNotFound())

        return Err(AccountRuleError("INVALID_STATE_TRANSITION", existing.version))

    if expected_version != 0:
        return Err(AccountRuleError("VERSION_CONFLICT"))

    patient = await booking_patient(db, context, payload.patient_id, payload.starts_at)

    if isinstance(patient, Err):
        return patient

    responsible = await booking_responsible(
        db,
        context,
        payload.patient_id,
        payload.responsible_contact_id,
        payload.starts_at,
        required=patient.value.identification_basis == "minor_without_document",
    )

    if isinstance(responsible, Err):
        return responsible

    service = await booking_service(
        db, context, payload.professional_id, payload.service_id
    )

    if isinstance(service, Err):
        return service

    professional = await account_professional(db, context, payload.professional_id)

    if isinstance(professional, Err):
        return professional

    busy = await occupancy(
        db, payload.professional_id, payload.starts_at, payload.ends_at
    )
    duration = int((payload.ends_at - payload.starts_at).total_seconds() // 60)
    available = await available_schedule(
        db,
        context,
        payload.professional_id,
        payload.starts_at,
        payload.ends_at,
        duration,
        occupied=busy,
    )

    if isinstance(available, Err):
        return available

    if not available.value:
        return Err(AccountRuleError("SLOT_UNAVAILABLE"))

    now = await dao_appointments.server_time(db)
    account = context.account
    values = {
        **payload.model_dump(),
        "id": entity_key,
        "account_id": account.id,
        "status": "scheduled",
        "confirmed_at": None,
        "version": 1,
        "service_name_snapshot": service.value.name,
        "offered_duration_minutes_snapshot": service.value.effective_duration_minutes,
        "professional_name_snapshot": professional.value.public_name,
        "location_name_snapshot": account.location_name,
        "location_address_snapshot": account.location_address,
        "location_country_snapshot": account.location_country,
        "location_state_snapshot": account.location_state,
        "location_city_snapshot": account.location_city,
        "time_zone_snapshot": account.time_zone,
        "created_at": now,
        "updated_at": now,
    }
    state = AppointmentResponse.model_validate(values)
    await dao_appointments.create(db, obj_in=values, commit=False)
    await record_history(db, context, state, "created", now)

    return Ok(
        AccountEffect(
            state,
            state.version,
            [
                AccountChange(
                    "appointment", str(entity_key), state, state.version, "members"
                )
            ],
            False,
        )
    )


async def record_history(
    db: AsyncSession,
    context: AccountContext,
    state: AppointmentResponse,
    action: str,
    now: datetime,
    reason: str | None = None,
) -> None:
    try:
        history = AppointmentHistoryResponse.model_validate(
            {
                **state.model_dump(include=set(AppointmentState.model_fields)),
                "appointment_id": state.id,
                "account_id": state.account_id,
                "action": action,
                "actor_kind": "staff",
                "actor_user_id": context.actor.user_id,
                "actor_contact_person_id": None,
                "change_reason": reason,
                "changed_at": now,
            }
        )
    except ValidationError as error:
        raise DAOError("La historia no cumple su esquema") from error

    await dao_histories.append(db, history.model_dump())


def appointment_state_response(
    row: Appointment | AppointmentHistory,
) -> dict[str, object]:
    return {
        "responsible_contact_id": row.responsible_contact_id,
        "starts_at": row.starts_at,
        "ends_at": row.ends_at,
        "status": row.status,
        "confirmed_at": row.confirmed_at,
        "version": row.version,
        "service_name_snapshot": row.service_name_snapshot,
        "offered_duration_minutes_snapshot": row.offered_duration_minutes_snapshot,
        "professional_name_snapshot": row.professional_name_snapshot,
        "location_name_snapshot": row.location_name_snapshot,
        "location_address_snapshot": row.location_address_snapshot,
        "location_country_snapshot": row.location_country_snapshot,
        "location_state_snapshot": row.location_state_snapshot,
        "location_city_snapshot": row.location_city_snapshot,
        "time_zone_snapshot": row.time_zone_snapshot,
    }


def appointment_response(row: Appointment) -> dict[str, object]:
    return {
        **appointment_state_response(row),
        "id": row.id,
        "account_id": row.account_id,
        "patient_id": row.patient_id,
        "professional_id": row.professional_id,
        "service_id": row.service_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def history_response(row: AppointmentHistory) -> dict[str, object]:
    return {
        **appointment_state_response(row),
        "appointment_id": row.appointment_id,
        "account_id": row.account_id,
        "action": row.action,
        "actor_kind": row.actor_kind,
        "actor_user_id": row.actor_user_id,
        "actor_contact_person_id": row.actor_contact_person_id,
        "change_reason": row.change_reason,
        "changed_at": row.changed_at,
    }


async def captured_history(
    db: AsyncSession, state: AppointmentResponse
) -> AppointmentHistoryProjection:
    """Project only history confirmed by this appointment version."""
    rows, _ = await dao_histories.get_multi(
        db,
        where={"appointment_id": state.id, "account_id": state.account_id},
        ordering=[("version", False)],
        shows=None,
    )

    return AppointmentHistoryProjection(
        appointment_id=state.id,
        account_id=state.account_id,
        version=state.version,
        starts_at=state.starts_at,
        ends_at=state.ends_at,
        items=[
            AppointmentHistoryResponse.model_validate(history_response(row))
            for row in rows
            if row.version <= state.version
        ],
    )


async def read_appointments(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: AppointmentQuery | None = None,
    appointment_id: UUID | None = None,
    history_query: AppointmentHistoryQuery | None = None,
) -> Result[
    dict[str, object],
    InvalidCredential | AccountNotFound | AccountObjectNotFound | AccessDenied,
]:
    async with transaction(db):
        identity = await authenticate(db, credential)

        if isinstance(identity, Err):
            return identity

        scope = await account_context(
            db, identity.value, account_id, require_device=True
        )

        if isinstance(scope, Err):
            return scope

        if scope.value.account.status != "active":
            return Err(AccessDenied())

        if appointment_id is not None:
            row = await dao_appointments.get_by(
                db, where={"id": appointment_id, "account_id": account_id}
            )

            if row is Empty:
                return Err(AccountObjectNotFound())

            if history_query is None:
                response = appointment_response(row)
            else:
                histories, total = await dao_histories.page(
                    db, account_id, appointment_id, history_query
                )
                response = {
                    "items": [history_response(item) for item in histories],
                    "total": total,
                }
        elif query is not None:
            rows, total = await dao_appointments.page(db, account_id, query)
            response = {
                "items": [appointment_response(row) for row in rows],
                "total": total,
            }
        else:
            return Err(AccountObjectNotFound())

    return Ok(response)


async def read_availability(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    query: AvailabilityQuery,
) -> Result[
    dict[str, object],
    InvalidCredential
    | AccountNotFound
    | AccountObjectNotFound
    | AccessDenied
    | AccountRuleError,
]:
    async with transaction(db):
        identity = await authenticate(db, credential)

        if isinstance(identity, Err):
            return identity

        scope = await account_context(
            db, identity.value, account_id, require_device=True
        )

        if isinstance(scope, Err):
            return scope

        service = await booking_service(
            db, scope.value, query.professional_id, query.service_id
        )

        if isinstance(service, Err):
            return service

        reference = service.value.effective_duration_minutes
        duration = (
            reference if query.duration_minutes is None else query.duration_minutes
        )
        busy = await occupancy(db, query.professional_id, query.from_, query.until)
        available = await available_schedule(
            db,
            scope.value,
            query.professional_id,
            query.from_,
            query.until,
            duration,
            occupied=busy,
        )

        if isinstance(available, Err):
            return available

        response: dict[str, object] = {
            "account_id": account_id,
            "professional_id": query.professional_id,
            "service_id": query.service_id,
            "reference_duration_minutes": reference,
            "requested_duration_minutes": duration,
            "available_intervals": [
                interval.model_dump() for interval in available.value
            ],
        }

    return Ok(response)
