from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.application.management_cases import (
    account_professional,
    catalog_accounts,
    own_professional,
)
from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
    ProfessionalResponse,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.authorization.application.authorization_cases import authenticate
from src.api.authorization.domain.authorization import AuthenticatedActor
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.services.application.offers_cases import offer_response
from src.api.services.domain.services import (
    CreateServicePayload,
    ServicePatch,
    ServiceQuery,
    ServiceResponse,
    ServiceStatusPayload,
)
from src.api.services.repository.dao import dao_offers, dao_services
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def service_permission(
    db: AsyncSession, context: AccountContext
) -> Result[ProfessionalResponse, AccessDenied | AccountObjectNotFound]:
    if not context.owner:
        return Err(AccessDenied())

    professional = await own_professional(db, context.actor.user_id)

    if isinstance(professional, Err):
        return professional

    return await account_professional(db, context, professional.value.id, own=True)


async def service_projection_accounts(
    db: AsyncSession,
    actor: AuthenticatedActor,
    account_id: UUID,
    entity_key: UUID | dict[str, UUID],
) -> list[UUID]:
    targets = await catalog_accounts(db, actor.user_id, account_id)
    professional = await own_professional(db, actor.user_id)

    if isinstance(professional, Ok) and isinstance(entity_key, UUID):
        offers = await dao_offers.for_service(db, professional.value.id, entity_key)
        targets.extend(row.account_id for row in offers)

    return sorted(set(targets) | {account_id})


async def apply_service_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID | dict[str, UUID],
    expected_version: int,
    payload: BaseModel | None,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    if not context.owner:
        return Err(AccessDenied())

    if not isinstance(entity_key, UUID):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if not (
        action == "CreateService"
        and isinstance(payload, CreateServicePayload)
        or action == "UpdateService"
        and isinstance(payload, ServicePatch)
        or action == "SetServiceStatus"
        and isinstance(payload, ServiceStatusPayload)
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    data = payload

    row = await dao_services.get(
        db, entity_key, execution_options={"populate_existing": True}
    )

    if isinstance(data, CreateServicePayload):
        professional_id = data.professional_id
    elif row is Empty:
        return Err(AccountObjectNotFound())
    else:
        professional_id = row.professional_id

    scope = await account_professional(db, context, professional_id, own=True)

    if isinstance(scope, Err):
        return scope

    now = await dao_services.server_time(db)

    if isinstance(data, CreateServicePayload):
        if expected_version != 0:
            return Err(AccountRuleError("VERSION_CONFLICT"))

        if row is not Empty:
            return Err(AccountRuleError("INVALID_STATE_TRANSITION"))

        row = await dao_services.create(
            db,
            obj_in={
                **data.model_dump(),
                "id": entity_key,
                "created_at": now,
                "updated_at": now,
            },
            commit=False,
        )
    else:
        if row.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", row.version))

        values = data.model_dump(exclude_unset=True)

        if all(getattr(row, name) == value for name, value in values.items()):
            return Err(AccountRuleError("NO_CHANGES", row.version))

        row = await dao_services.revise(db, row, values, now)

    state = ServiceResponse.model_validate(row)
    targets = await catalog_accounts(db, context.actor.user_id, context.account.id)
    changes = [
        AccountChange("service", str(entity_key), state, state.version, "owner", target)
        for target in targets
    ]

    for offer in await dao_offers.for_service(db, row.professional_id, row.id):
        projected = offer_response(offer, row)
        key = {"professionalId": str(row.professional_id), "serviceId": str(row.id)}
        changes.append(
            AccountChange(
                "service_offer",
                key,
                projected,
                projected["version"],
                "members",
                offer.account_id,
            )
        )

    return Ok(AccountEffect(state, state.version, changes, False))


async def read_catalog(
    db: AsyncSession, credential: str | None, query: ServiceQuery
) -> Result[dict[str, object], InvalidCredential | AccountObjectNotFound]:
    async with transaction(db):
        identity = await authenticate(db, credential)

        if isinstance(identity, Err):
            return identity

        professional = await own_professional(db, identity.value.user_id)

        if isinstance(professional, Err):
            return professional

        rows, total = await dao_services.page(db, professional.value.id, query)
        response: dict[str, object] = {
            "items": [
                {
                    "id": row.id,
                    "professional_id": row.professional_id,
                    "name": row.name,
                    "default_duration_minutes": row.default_duration_minutes,
                    "status": row.status,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "version": row.version,
                }
                for row in rows
            ],
            "total": total,
        }

    return Ok(response)
