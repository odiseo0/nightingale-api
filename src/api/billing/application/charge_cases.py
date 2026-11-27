from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.accounts.application.accounts_cases import account_context
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
from src.api.appointments.application.appointments_cases import encounter_appointment
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.billing.domain.charges import (
    BalanceView,
    CancelPatientChargePayload,
    Charge,
    ChargeHasActivePaymentsError,
    ChargeNotDraftError,
    ChargeResponse,
    CreatePatientChargePayload,
    IssuePatientChargePayload,
    Money,
    UpdatePatientChargePayload,
    cancel,
    issue,
    update_draft,
)
from src.api.billing.domain.money import charge_balance
from src.api.billing.repository.dao import (
    dao_charge_histories,
    dao_charges,
    dao_payments,
)
from src.api.encounters.application.encounters_cases import encounter_for_record
from src.api.patients.application.patients_cases import clinical_patient
from src.api.services.application.services_cases import (
    charge_service_reference,
    resolve_service_price,
)
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.billing.repository.models import PatientCharge


def charge_projection(row: PatientCharge, paid, outstanding, state) -> ChargeResponse:
    return ChargeResponse(
        charge_id=row.id,
        patient_id=row.patient_id,
        appointment_id=row.appointment_id,
        encounter_id=row.encounter_id,
        service_id=row.service_id,
        description=row.description,
        amount=row.amount,
        currency=row.currency,
        price_source=row.price_source,
        status=row.status,
        balance=BalanceView(paid=paid, outstanding=outstanding, state=state),
        issued_at=row.issued_at,
        cancelled_at=row.cancelled_at,
        created_at=row.created_at,
        version=row.version,
    )


async def charge_effect(
    db: AsyncSession, row: PatientCharge, account_id: UUID
) -> AccountEffect:
    """Projection with the current balance; drafts stay invisible to the patient,
    so the audience is the closed financial one (§16.1)."""
    amounts = await dao_payments.active_amounts_of(db, row.id, account_id)
    balance = charge_balance(row.amount, amounts)
    state = charge_projection(row, balance.paid, balance.outstanding, balance.state)

    return AccountEffect(
        state,
        state.version,
        [
            AccountChange(
                "billing_charge",
                str(row.id),
                state,
                state.version,
                "billing",
                account_id,
            )
        ],
        False,
    )


def _domain_charge(row: PatientCharge) -> Charge:
    return Charge(
        charge_id=row.id,
        account_id=row.account_id,
        patient_id=row.patient_id,
        appointment_id=row.appointment_id,
        encounter_id=row.encounter_id,
        service_id=row.service_id,
        description=row.description,
        amount=Money(amount=row.amount, currency=row.currency),
        price_source=row.price_source,
        status=row.status,
        issued_at=row.issued_at,
        cancelled_at=row.cancelled_at,
        cancellation_reason=row.cancellation_reason,
        created_by=row.created_by,
        version=row.version,
    )


async def apply_charge_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID | dict[str, UUID],
    expected_version: int,
    payload: BaseModel | None,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    """Staff charge lifecycle (§8, §15.2). Never automatic from appointments or
    encounters; every write keeps its history in the same transaction (D25)."""
    if not context.owner and not context.billing_permissions.granted("billing_charges"):
        return Err(AccessDenied())

    if not isinstance(entity_key, UUID):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if not (
        action == "CreatePatientCharge"
        and isinstance(payload, CreatePatientChargePayload)
        or action == "UpdatePatientCharge"
        and isinstance(payload, UpdatePatientChargePayload)
        or action == "IssuePatientCharge"
        and isinstance(payload, IssuePatientChargePayload)
        or action == "CancelPatientCharge"
        and isinstance(payload, CancelPatientChargePayload)
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    account_id = context.account.id
    now = datetime_now()

    if action == "CreatePatientCharge":
        data = payload

        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if await clinical_patient(db, account_id, data.patient_id) is Empty:
            return Err(AccountObjectNotFound())

        if not await encounter_appointment(
            db, account_id, data.patient_id, data.appointment_id
        ):
            return Err(AccountObjectNotFound())

        if not await encounter_for_record(
            db, account_id, data.patient_id, data.encounter_id
        ):
            return Err(AccountObjectNotFound())

        description = data.description
        price_source = "manual"
        if data.amount is not None:
            amount, currency = data.amount, data.currency
        else:
            # Price resolved through the public services case; the charge freezes
            # its own snapshot and later catalog changes never rewrite it (D25).
            reference = await charge_service_reference(db, account_id, data.service_id)

            if reference is None:
                return Err(AccountObjectNotFound())

            resolved = await resolve_service_price(
                db, account_id, reference["professional_id"], data.service_id
            )

            if resolved is None:
                return Err(AccountRuleError("PRICE_NOT_DEFINED"))

            amount, currency = resolved.amount, resolved.currency
            price_source = resolved.source
            description = description or reference["name"]

        row = await dao_charges.create(
            db,
            commit=False,
            obj_in={
                "id": entity_key,
                "account_id": account_id,
                "patient_id": data.patient_id,
                "appointment_id": data.appointment_id,
                "encounter_id": data.encounter_id,
                "service_id": data.service_id,
                "description": description,
                "amount": amount,
                "currency": currency,
                "price_source": price_source,
                "created_by": context.actor.user_id,
            },
        )
        await dao_charge_histories.insert_entry(
            db,
            uuid7(),
            row.id,
            account_id,
            "created",
            row.version,
            context.actor.user_id,
            data.adjust_reason,
            now,
        )

        return Ok(await charge_effect(db, row, account_id))

    row = await dao_charges.by_id_for_update(db, entity_key, account_id)

    if row is Empty:
        return Err(AccountObjectNotFound())

    if row.version != expected_version:
        return Err(AccountRuleError("VERSION_CONFLICT", row.version))

    try:
        if action == "UpdatePatientCharge":
            data = payload
            updated = update_draft(
                _domain_charge(row),
                description=data.description,
                amount=None
                if data.amount is None
                else Money(amount=data.amount, currency=data.currency),
                adjust_reason=data.adjust_reason,
            )
            values = {
                "description": updated.description,
                "amount": updated.amount.amount,
                "currency": updated.amount.currency,
                "price_source": updated.price_source,
            }
            history_action = (
                "amount_adjusted"
                if "amount" in data.model_fields_set
                else "draft_updated"
            )
            reason = data.adjust_reason
        elif action == "IssuePatientCharge":
            updated = issue(_domain_charge(row), now)
            values = {"status": "issued", "issued_at": updated.issued_at}
            history_action, reason = "issued", None
        else:
            active = await dao_payments.active_amounts_of(db, row.id, account_id)
            updated = cancel(
                _domain_charge(row),
                now,
                payload.reason,
                has_active_payments=bool(active),
            )
            values = {
                "status": "cancelled",
                "cancelled_at": updated.cancelled_at,
                "cancellation_reason": updated.cancellation_reason,
            }
            history_action, reason = "cancelled", payload.reason
    except ChargeHasActivePaymentsError:
        return Err(AccountRuleError("CHARGE_HAS_ACTIVE_PAYMENTS", row.version))
    except ChargeNotDraftError:
        return Err(AccountRuleError("CHARGE_NOT_DRAFT", row.version))

    applied = await dao_charges.apply_update(
        db, row.id, account_id, row.version, values
    )

    if not applied:
        return Err(AccountRuleError("VERSION_CONFLICT", row.version))

    await dao_charge_histories.insert_entry(
        db,
        uuid7(),
        row.id,
        account_id,
        history_action,
        row.version + 1,
        context.actor.user_id,
        reason,
        now,
    )
    refreshed = await dao_charges.by_id_in_account(db, row.id, account_id)

    return Ok(await charge_effect(db, refreshed, account_id))


async def read_charges(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    page: int,
    shows: int,
    patient_id: UUID | None = None,
    status: str | None = None,
) -> Result[dict[str, object], InvalidCredential | AccessDenied | AccountNotFound]:
    """Financial list; authorization precedes counting and paging (§15.2)."""
    async with transaction(db):
        scope = await billing_scope(db, credential, account_id)

        if isinstance(scope, Err):
            return scope

        rows, total = await dao_charges.page_list(
            db, account_id, page, shows, patient_id=patient_id, status=status
        )
        items = []
        for row in rows:
            amounts = await dao_payments.active_amounts_of(db, row.id, account_id)
            balance = charge_balance(row.amount, amounts)
            items.append(
                charge_projection(row, balance.paid, balance.outstanding, balance.state)
            )
        response: dict[str, object] = {"items": items, "total": total}

    return Ok(response)


async def read_charge_detail(
    db: AsyncSession, credential: str | None, account_id: UUID, charge_id: UUID
) -> Result[ChargeResponse, InvalidCredential | AccessDenied | AccountObjectNotFound]:
    async with transaction(db):
        scope = await billing_scope(db, credential, account_id)

        if isinstance(scope, Err):
            return scope

        row = await dao_charges.by_id_in_account(db, charge_id, account_id)

        if row is Empty:
            return Err(AccountObjectNotFound())

        amounts = await dao_payments.active_amounts_of(db, row.id, account_id)
        balance = charge_balance(row.amount, amounts)
        response = charge_projection(
            row, balance.paid, balance.outstanding, balance.state
        )

    return Ok(response)


async def billing_scope(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    action: str = "billing_read",
) -> Result[AccountContext, InvalidCredential | AccessDenied | AccountNotFound]:
    """Financial routes re-authorize on every request; the owner always passes
    and assistants need the explicit D27 grant."""
    identity = await authenticate(db, credential)

    if isinstance(identity, Err):
        return identity

    scope = await account_context(db, identity.value, account_id, require_device=True)

    if isinstance(scope, Err):
        return scope

    context = scope.value

    if not context.owner and not context.billing_permissions.granted(action):
        return Err(AccessDenied())

    return Ok(context)
