import hashlib
import secrets
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.appointments.application.appointments_cases import grant_anchor_appointment
from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.billing.domain.payments import (
    GrantCreateRequest,
    GrantIssuedResponse,
    GrantResponse,
)
from src.api.billing.repository.dao import dao_charges, dao_grants
from src.core import Err, Ok, Result
from src.core.utils.utils import Empty, datetime_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.accounts.domain.accounts import AccountContext
    from src.api.billing.repository.models import PatientBillingGrant

# A charge-only grant has no appointment anchor; D28 bounds it to 30 days.
CHARGE_GRANT_DAYS = 30


def grant_status(row: PatientBillingGrant) -> str:
    if row.revoked_at is not None:
        return "revoked"
    if row.expires_at <= datetime_now():
        return "expired"
    return "active"


def grant_response(row: PatientBillingGrant) -> GrantResponse:
    return GrantResponse(
        grant_id=row.id,
        patient_id=row.patient_id,
        appointment_id=row.appointment_id,
        charge_id=row.charge_id,
        actions=row.actions,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        status=grant_status(row),
    )


async def issue_grant(
    db: AsyncSession, context: AccountContext, data: GrantCreateRequest
) -> Result[GrantIssuedResponse, AccountObjectNotFound | AccountRuleError]:
    """Limited patient link by concrete object and action (D28). Only the hash
    of the secret is stored; the secret is delivered exactly once."""
    account_id = context.account.id
    existing = await dao_grants.get(db, data.operation_id)

    if existing is not Empty:
        if existing.account_id != account_id:
            return Err(AccountObjectNotFound())

        # Idempotent retry: the secret cannot be recovered, only re-read.
        return Ok(
            GrantIssuedResponse(
                grant_id=existing.id,
                secret=None,
                duplicate=True,
                actions=existing.actions,
                expires_at=existing.expires_at,
            )
        )

    now = datetime_now()

    if data.appointment_id is not None:
        anchor = await grant_anchor_appointment(
            db, account_id, data.patient_id, data.appointment_id
        )

        if anchor is None:
            return Err(AccountObjectNotFound())

        expires_at = anchor + timedelta(days=CHARGE_GRANT_DAYS)
    else:
        charge = await dao_charges.by_id_in_account(db, data.charge_id, account_id)

        if charge is Empty or charge.patient_id != data.patient_id:
            return Err(AccountObjectNotFound())

        expires_at = now + timedelta(days=CHARGE_GRANT_DAYS)

    secret = secrets.token_hex(32)
    await dao_grants.insert_grant(
        db,
        {
            "id": data.operation_id,
            "account_id": account_id,
            "patient_id": data.patient_id,
            "appointment_id": data.appointment_id,
            "charge_id": data.charge_id,
            "token_hash": hashlib.sha256(secret.encode()).hexdigest(),
            "actions": sorted(set(data.actions)),
            "expires_at": expires_at,
            "created_by": context.actor.user_id,
        },
    )
    await record_control(
        db,
        ControlAudit(
            account_id=account_id,
            actor_user_id=context.actor.user_id,
            actor_device_id=context.actor.device_id,
            action="IssuePatientBillingGrant",
            object_type="patient_billing_grant",
            object_key=str(data.operation_id),
            outcome="accepted",
            correlation_id=uuid7(),
            occurred_at=now,
        ),
    )

    return Ok(
        GrantIssuedResponse(
            grant_id=data.operation_id,
            secret=secret,
            actions=sorted(set(data.actions)),
            expires_at=expires_at,
        )
    )


async def revoke_grant(
    db: AsyncSession, context: AccountContext, grant_id: UUID
) -> Result[GrantResponse, AccountObjectNotFound]:
    """Revocation takes effect immediately; a report already submitted keeps
    its history and stays reviewable (§9.5)."""
    account_id = context.account.id
    row = await dao_grants.get_by(
        db,
        where={"id": grant_id, "account_id": account_id},
        execution_options={"populate_existing": True},
    )

    if row is Empty:
        return Err(AccountObjectNotFound())

    now = datetime_now()

    if row.revoked_at is None:
        await dao_grants.revoke(db, grant_id, account_id, now)
        row = await dao_grants.get_by(
            db,
            where={"id": grant_id, "account_id": account_id},
            execution_options={"populate_existing": True},
        )
        await record_control(
            db,
            ControlAudit(
                account_id=account_id,
                actor_user_id=context.actor.user_id,
                actor_device_id=context.actor.device_id,
                action="RevokePatientBillingGrant",
                object_type="patient_billing_grant",
                object_key=str(grant_id),
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=now,
            ),
        )

    return Ok(grant_response(row))


async def list_grants(
    db: AsyncSession,
    account_id: UUID,
    page: int,
    shows: int,
    patient_id: UUID | None = None,
    charge_id: UUID | None = None,
) -> dict[str, object]:
    rows, total = await dao_grants.page_grants(
        db, account_id, page, shows, patient_id=patient_id, charge_id=charge_id
    )

    return {"items": [grant_response(row) for row in rows], "total": total}


async def revoke_appointment_grants(
    db: AsyncSession, account_id: UUID, appointment_id: UUID, revoked_at
) -> int:
    """Public case used by the appointment cancellation: anchored grants are
    revoked in the same acceptance (D28). Returns how many were revoked."""
    return await dao_grants.revoke_by_appointment(
        db, appointment_id, account_id, revoked_at
    )
