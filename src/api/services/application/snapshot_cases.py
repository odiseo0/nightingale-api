from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.domain.accounts import AccountContext, ProfessionalResponse
from src.api.services.application.offers_cases import offer_response
from src.api.services.domain.offers import ServiceOfferResponse
from src.api.services.domain.services import ServiceResponse
from src.api.services.repository.dao import dao_offers, dao_services
from src.api.sync.domain.downloads import SyncItem
from src.core.db import DAOError
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def snapshot_services(
    db: AsyncSession, context: AccountContext, professionals: list[ProfessionalResponse], required_services: set[UUID],
) -> list[SyncItem]:
    items: list[SyncItem] = []
    offers, _ = await dao_offers.get_multi(db, where={"account_id": context.account.id},
                                         ordering=[("professional_id", False), ("service_id", False)], shows=None)
    for row in offers:
        service = await dao_services.get(db, row.service_id)
        if service is Empty:
            raise DAOError("La oferta no tiene servicio")

        if (row.status != "active" or service.status != "active") and row.service_id not in required_services:
            continue

        state = ServiceOfferResponse.model_validate(offer_response(row, service))
        items.append(SyncItem(entity_type="service_offer", entity_key={"professionalId": row.professional_id, "serviceId": row.service_id},
                              entity_version=row.version, state=state))

    if context.owner:
        own = [row.id for row in professionals if row.user_id == context.actor.user_id]
        services, _ = await dao_services.get_multi(db, where={"professional_id": own}, ordering=[("id", False)], shows=None)
        items.extend(SyncItem(entity_type="service", entity_key=row.id, entity_version=row.version,
                              state=ServiceResponse.model_validate(row)) for row in services)

    return items
