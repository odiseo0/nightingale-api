from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from src.api.accounts.domain.accounts import (
    AccessResponse,
    AccountContext,
    AccountDetails,
    AccountDeviceResponse,
    AccountResponse,
    AccountSummary,
    BootstrapPracticeInput,
    MeResponse,
    PracticeCreated,
    ProfessionalResponse,
)
from src.api.accounts.domain.errors import (
    AccountNotFound,
    DeviceAlreadyRegistered,
    DeviceVersionConflict,
    PracticeAlreadyExists,
    ProfessionalNotFound,
    UnknownTimeZone,
)
from src.api.accounts.repository.dao import (
    dao_account_devices,
    dao_account_professionals,
    dao_accounts,
    dao_memberships,
    dao_professionals,
)
from src.api.audit.application.audit_cases import record_control
from src.api.audit.domain.audit import ControlAudit
from src.api.authorization.application.authorization_cases import (
    authenticate,
    ensure_identity,
    get_identity,
    get_own_device,
)
from src.api.authorization.domain.authorization import (
    AuthenticatedActor,
    ExternalIdentity,
)
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.sync.application.sync_cases import create_head, get_permission_epoch
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import PageQuery, PaginatedResponse
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def bootstrap_practice(
    db: AsyncSession,
    obj_in: BootstrapPracticeInput,
) -> Result[PracticeCreated, AccessDenied | PracticeAlreadyExists | UnknownTimeZone]:
    async with transaction(db):
        if not await dao_accounts.can_bootstrap(db):
            return Err(AccessDenied())

        if not await dao_accounts.is_known_time_zone(db, obj_in.time_zone):
            return Err(UnknownTimeZone(obj_in.time_zone))

        now = await dao_accounts.get_server_time(db)
        identity = ExternalIdentity(
            obj_in.owner_issuer, obj_in.owner_subject, obj_in.owner_name
        )
        result = await ensure_identity(db, identity, now)

        match result:
            case Ok(user):
                pass
            case Err(error):
                return Err(error)

        existing = await dao_accounts.get_by(
            db,
            where={"owner_user_id": user.id, "kind": "independent"},
        )

        if existing is not Empty:
            return Err(PracticeAlreadyExists(user.id))

        professional = await dao_professionals.get_by(db, where={"user_id": user.id})

        if professional is not Empty and professional.status != "active":
            return Err(AccessDenied())

        details = obj_in.model_dump(include=set(AccountDetails.model_fields))
        account = await dao_accounts.create(
            db,
            commit=False,
            obj_in={
                **details,
                "id": uuid7(),
                "kind": "independent",
                "owner_user_id": user.id,
                "created_at": now,
                "updated_at": now,
            },
        )
        await dao_memberships.create_membership(
            db, account.id, user.id, now, commit=False
        )

        if professional is Empty:
            professional = await dao_professionals.create(
                db,
                commit=False,
                obj_in={
                    "id": uuid7(),
                    "user_id": user.id,
                    "public_name": obj_in.professional_name,
                    "created_at": now,
                    "updated_at": now,
                },
            )
        await dao_account_professionals.link(
            db,
            account.id,
            professional.id,
            user.id,
            now,
            commit=False,
        )
        await create_head(db, account.id, now)
        await record_control(
            db,
            ControlAudit(
                account_id=account.id,
                operator_ref="administrative-create-practice",
                action="CreatePractice",
                object_type="account",
                object_key=str(account.id),
                outcome="accepted",
                correlation_id=uuid7(),
                occurred_at=now,
            ),
        )
        created = PracticeCreated(
            user_id=user.id,
            account_id=account.id,
            professional_id=professional.id,
        )

    return Ok(created)


async def account_page(
    db: AsyncSession,
    actor: AuthenticatedActor,
    query: PageQuery,
) -> PaginatedResponse[AccountSummary]:
    accounts, total = await dao_accounts.get_visible(
        db,
        actor.user_id,
        offset=(query.page - 1) * query.shows,
        shows=query.shows,
    )

    return PaginatedResponse[AccountSummary](
        items=[
            AccountSummary(
                id=account.id,
                display_name=account.display_name,
                status=account.status,
                role="owner" if account.owner_user_id == actor.user_id else "assistant",
            )
            for account in accounts
        ],
        total=total,
    )


async def get_accounts(
    db: AsyncSession,
    credential: str | None,
    page: int = 1,
    shows: int = 100,
) -> Result[PaginatedResponse[AccountSummary], InvalidCredential]:
    query = PageQuery(page=page, shows=shows)

    async with transaction(db):
        result = await authenticate(db, credential)

        match result:
            case Ok(actor):
                response = await account_page(db, actor, query)
            case Err(error):
                return Err(error)

    return Ok(response)


async def get_me(
    db: AsyncSession, credential: str | None
) -> Result[MeResponse, InvalidCredential]:
    async with transaction(db):
        result = await authenticate(db, credential)

        match result:
            case Ok(actor):
                pass
            case Err(error):
                return Err(error)

        identity = await get_identity(db, actor)

        match identity:
            case Ok(user):
                pass
            case Err(error):
                return Err(error)

        accounts = await account_page(db, actor, PageQuery())
        response = MeResponse(
            user_id=user.id,
            display_name=user.display_name,
            status=user.status,
            oidc_issuer=user.oidc_issuer,
            oidc_subject=user.oidc_subject,
            accounts=accounts,
        )

    return Ok(response)


async def get_account_context(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
    require_device: bool,
) -> Result[AccountContext, InvalidCredential | AccountNotFound | AccessDenied]:
    """Join the caller's transaction so membership and device locks cover its read."""
    result = await authenticate(db, credential)

    match result:
        case Ok(actor):
            pass
        case Err(error):
            return Err(error)

    return await account_context(db, actor, account_id, require_device)


async def account_context(
    db: AsyncSession,
    actor: AuthenticatedActor,
    account_id: UUID,
    require_device: bool,
) -> Result[AccountContext, AccountNotFound | AccessDenied]:
    """Read current account permissions inside the caller's transaction."""
    row = await dao_accounts.get_for_member(db, actor.user_id, account_id)

    if row is Empty:
        return Err(AccountNotFound(account_id))

    account, membership = row
    owner = account.owner_user_id == actor.user_id

    if account.status != "active" and not owner:
        return Err(AccessDenied())

    registered = await dao_account_devices.get_scoped(db, account.id, actor.device_id)

    if require_device and (registered is Empty or registered.status != "active"):
        return Err(AccessDenied())

    return Ok(
        AccountContext(
            actor=actor,
            account=AccountResponse.model_validate(account),
            device_status=None if registered is Empty else registered.status,
            owner=owner,
        )
    )


async def register_own_device(
    db: AsyncSession,
    context: AccountContext,
    device_id: UUID,
    expected_version: int,
) -> Result[
    AccountDeviceResponse,
    AccessDenied | InvalidCredential | DeviceVersionConflict | DeviceAlreadyRegistered,
]:
    """The operation owns the transaction, identity locks and account control."""
    actor = context.actor

    if device_id != actor.device_id or context.account.status != "active":
        return Err(AccessDenied())

    existing = await dao_account_devices.get_scoped(db, context.account.id, device_id)

    if existing is not Empty and existing.status == "revoked":
        return Err(AccessDenied())

    if expected_version != 0:
        return Err(
            DeviceVersionConflict(None if existing is Empty else existing.version)
        )

    if existing is not Empty:
        return Err(DeviceAlreadyRegistered(existing.version))

    device = await get_own_device(db, actor)

    match device:
        case Ok(details):
            pass
        case Err(error):
            return Err(error)

    now = await dao_accounts.get_server_time(db)
    access = await dao_account_devices.register(
        db,
        context.account.id,
        actor.device_id,
        actor.user_id,
        now,
        commit=False,
    )

    return Ok(
        AccountDeviceResponse(
            device_id=access.device_id,
            display_name=details.display_name,
            status=access.status,
            client_version=details.client_version,
            local_schema_version=details.local_schema_version,
            last_seen_at=details.last_seen_at,
            version=access.version,
        )
    )


async def get_account(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
) -> Result[AccountResponse, InvalidCredential | AccountNotFound | AccessDenied]:
    async with transaction(db):
        result = await get_account_context(
            db, credential, account_id, require_device=True
        )

        match result:
            case Ok(context):
                response = context.account
            case Err(error):
                return Err(error)

    return Ok(response)


async def get_access(
    db: AsyncSession,
    credential: str | None,
    account_id: UUID,
) -> Result[AccessResponse, InvalidCredential | AccountNotFound | AccessDenied]:
    async with transaction(db):
        result = await get_account_context(
            db, credential, account_id, require_device=False
        )

        match result:
            case Ok(context):
                pass
            case Err(error):
                return Err(error)

        state = context.device_status or "registration_required"

        if context.account.status != "active":
            state = "inactive"

        epoch = await get_permission_epoch(db, account_id)
        response = AccessResponse(
            account_id=account_id,
            user_id=context.actor.user_id,
            device_id=context.actor.device_id,
            role="owner" if context.owner else "assistant",
            status=state,
            permission_epoch=epoch.value,
            allowed_actions=(
                (
                    ["RegisterAccountDevice"]
                    if state in ("active", "registration_required")
                    else []
                )
                + (
                    [
                        "RegisterPatient", "UpdatePatientProfile", "SetPatientProfileStatus",
                        "SetPatientCompletion", "AddPatientIdentifier",
                        "CreateContactPerson", "UpdateContactPerson", "SetContactPersonStatus",
                        "CreatePatientContactRelationship", "UpdatePatientContactRelationship", "SetPatientContactRelationshipStatus",
                        "CreateScheduleRule", "UpdateScheduleRule", "SetScheduleRuleStatus",
                        "CreateScheduleException", "UpdateScheduleException", "SetScheduleExceptionStatus",
                        "CreateScheduleBlock", "UpdateScheduleBlock", "SetScheduleBlockStatus",
                        "CreateAppointment",
                        "ConfirmAppointment",
                        "RescheduleAppointment",
                        "CancelAppointment",
                        "CompleteAppointment", "MarkAppointmentNoShow",
                    ]
                    if state == "active"
                    else []
                )
                + (
                    [
                        "CreateInvitation",
                        "RevokeInvitation",
                        "SetMembershipStatus",
                        "UpdateAccountDetails",
                        "UpdateAccountPolicy",
                        "SetAccountStatus",
                        "RevokeAccountDevice",
                        "RestoreAccountDevice",
                        "UpdateProfessionalProfile",
                        "CreateService", "UpdateService", "SetServiceStatus",
                        "OfferService", "UpdateServiceOffer", "SetServiceOfferStatus",
                    ]
                    if state == "active" and context.owner
                    else []
                )
                + (
                    ["SetAccountStatus"]
                    if state == "inactive"
                    and context.owner
                    and context.device_status == "active"
                    else []
                )
            ),
        )

    return Ok(response)


async def get_professional(
    db: AsyncSession,
    credential: str | None,
) -> Result[ProfessionalResponse, InvalidCredential | ProfessionalNotFound]:
    async with transaction(db):
        result = await authenticate(db, credential)

        match result:
            case Ok(actor):
                pass
            case Err(error):
                return Err(error)

        professional = await dao_professionals.get_by(
            db, where={"user_id": actor.user_id}
        )

        if professional is Empty:
            return Err(ProfessionalNotFound(actor.user_id))

        response = ProfessionalResponse.model_validate(professional)

    return Ok(response)


async def audit_scope(db: AsyncSession, user_id: UUID, account_id: UUID) -> bool:
    membership = await dao_memberships.get_by(
        db, where={"account_id": account_id, "user_id": user_id}
    )

    return membership is not Empty
