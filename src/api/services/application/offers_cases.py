from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

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
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.services.domain.offers import (
    OfferServicePayload,
    ServiceOfferProjection,
    ServiceOfferQuery,
    ServiceOfferResponse,
    UpdateServiceOfferPayload,
)
from src.api.services.domain.services import ServiceStatusPayload
from src.api.services.repository.dao import dao_offers, dao_services
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.api.services.repository.models import ProfessionalService, Service


def offer_response(
    row: ProfessionalService, service: Service
) -> ServiceOfferProjection:
    return {
        "account_id": row.account_id,
        "professional_id": row.professional_id,
        "service_id": row.service_id,
        "name": service.name,
        "default_duration_minutes": service.default_duration_minutes,
        "duration_minutes_override": row.duration_minutes_override,
        "effective_duration_minutes": service.default_duration_minutes
        if row.duration_minutes_override is None
        else row.duration_minutes_override,
        "status": row.status,
        "service_status": service.status,
        "service_version": service.version,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "version": row.version,
    }


async def booking_service(db: AsyncSession, context, professional_id, service_id):
    """Resolve the reference inside the future authorized appointment transaction."""
    scope = await account_professional(db, context, professional_id)

    if isinstance(scope, Err):
        return scope

    row = await dao_offers.get_by(
        db,
        where={
            "account_id": context.account.id,
            "professional_id": professional_id,
            "service_id": service_id,
        },
        execution_options={"populate_existing": True},
    )

    if row is Empty:
        return Err(AccountObjectNotFound())

    service = await dao_services.get(
        db, service_id, execution_options={"populate_existing": True}
    )

    if (
        context.account.status != "active"
        or row.status != "active"
        or service.status != "active"
    ):
        return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

    return Ok(ServiceOfferResponse.model_validate(offer_response(row, service)))


async def apply_offer_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID | dict[str, UUID],
    expected_version: int,
    payload: BaseModel | None,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if not context.owner:
        return Err(AccessDenied())

    if not isinstance(entity_key, dict) or set(entity_key) != {
        "professionalId",
        "serviceId",
    }:
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if not (
        action == "OfferService"
        and isinstance(payload, OfferServicePayload)
        or action == "UpdateServiceOffer"
        and isinstance(payload, UpdateServiceOfferPayload)
        or action == "SetServiceOfferStatus"
        and isinstance(payload, ServiceStatusPayload)
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    data = payload

    professional_id, service_id = entity_key["professionalId"], entity_key["serviceId"]
    scope = await account_professional(db, context, professional_id, own=True)

    if isinstance(scope, Err):
        return scope

    service = await dao_services.get(
        db, service_id, execution_options={"populate_existing": True}
    )

    if service is Empty or service.professional_id != professional_id:
        return Err(AccountObjectNotFound())

    key = {
        "account_id": context.account.id,
        "professional_id": professional_id,
        "service_id": service_id,
    }
    row = await dao_offers.get_by(
        db, where=key, execution_options={"populate_existing": True}
    )
    now = await dao_services.server_time(db)

    if action == "OfferService":
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if row is not Empty:
            return Err(AccountRuleError("NO_CHANGES", row.version))

        row = await dao_offers.create_offer(
            db,
            {**key, **data.model_dump(), "created_at": now, "updated_at": now},
            commit=False,
        )
    else:
        if row is Empty:
            return Err(AccountObjectNotFound())

        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        values = data.model_dump()

        if all(getattr(row, name) == value for name, value in values.items()):
            return Err(AccountRuleError("NO_CHANGES", row.version))

        row = await dao_offers.revise(db, row, values, now)

    state = offer_response(row, service)
    public_key = {name: str(value) for name, value in entity_key.items()}

    return Ok(
        AccountEffect(
            state,
            state["version"],
            [
                AccountChange(
                    "service_offer", public_key, state, state["version"], "members"
                )
            ],
            False,
        )
    )


async def read_offers(
    db: AsyncSession, credential: str | None, account_id: UUID, query: ServiceOfferQuery
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

        rows, total = await dao_offers.page(db, account_id, query)
        response: dict[str, object] = {
            "items": [offer_response(row, service) for row, service in rows],
            "total": total,
        }

    return Ok(response)
