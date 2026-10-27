from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from src.api.accounts.domain.accounts import (
    AccountChange,
    AccountContext,
    AccountEffect,
    AccountResponse,
    CreateInvitationPayload,
    InvitationAcceptanceResult,
    InvitationQuery,
    InvitationResponse,
    MemberResponse,
    MembershipStatusPayload,
)
from src.api.accounts.domain.errors import AccountObjectNotFound, AccountRuleError
from src.api.accounts.repository.dao import (
    dao_account_devices,
    dao_accounts,
    dao_invitations,
    dao_memberships,
)
from src.api.authorization.application.authorization_cases import (
    authenticate,
    identified_users,
)
from src.api.authorization.domain.errors import AccessDenied
from src.core import Err, Ok, Result
from src.core.db import transaction
from src.core.schema import BaseModel, PaginatedResponse
from src.core.utils.utils import Empty

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def invitation_view(row, now) -> InvitationResponse:
    response = InvitationResponse.model_validate(row)

    if response.status == "pending" and response.expires_at <= now:
        response.status = "expired"

    return response


async def invitation_target(db: AsyncSession, actor, invitation_id: UUID):
    row = await dao_invitations.get_by(
        db, where={"id": invitation_id, "invitee_user_id": actor.user_id}
    )

    if row is Empty:
        return Err(AccountObjectNotFound())

    return Ok(row.account_id)


async def invitation_context(
    db: AsyncSession, actor, account_id: UUID, invitation_id: UUID
):
    row = await dao_invitations.get_scoped(db, invitation_id, account_id)

    if row is Empty or row.invitee_user_id != actor.user_id:
        return Err(AccountObjectNotFound())

    account = await dao_accounts.get_for_update(
        db, account_id, execution_options={"populate_existing": True}
    )

    if account is Empty or account.kind != "independent" or account.status != "active":
        return Err(AccessDenied())

    membership = await dao_memberships.get_scoped(db, account_id, actor.user_id)

    if row.status == "accepted" and (
        membership is Empty or membership.status != "active"
    ):
        return Err(AccessDenied())

    device = await dao_account_devices.get_scoped(db, account_id, actor.device_id)

    if device is not Empty and device.status == "revoked":
        return Err(AccessDenied())

    return Ok(
        AccountContext(
            actor=actor,
            account=AccountResponse.model_validate(account),
            owner=account.owner_user_id == actor.user_id,
            device_status=None if device is Empty else device.status,
        )
    )


async def apply_invitation_operation(
    db: AsyncSession,
    context: AccountContext,
    action: str,
    entity_key: UUID,
    expected_version: int,
    payload: BaseModel | None,
    operation_id: UUID,
) -> Result[AccountEffect, AccessDenied | AccountObjectNotFound | AccountRuleError]:
    now = await dao_accounts.get_server_time(db)

    if action != "AcceptInvitation" and not context.owner:
        return Err(AccessDenied())

    if not isinstance(entity_key, UUID):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if payload is None:
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if (
        action not in ("CreateInvitation", "SetMembershipStatus")
        and payload.model_fields_set
    ):
        return Err(AccountRuleError("VALIDATION_ERROR"))

    if action == "SetMembershipStatus":
        if not isinstance(payload, MembershipStatusPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        data = payload

        if entity_key == context.account.owner_user_id:
            return Err(AccessDenied())

        membership = await dao_memberships.get_scoped(
            db, context.account.id, entity_key
        )

        if membership is Empty:
            return Err(AccountObjectNotFound())

        if membership.version != expected_version:
            return Err(AccountRuleError("VERSION_CONFLICT", membership.version))

        if membership.status == data.status:
            return Err(AccountRuleError("NO_CHANGES", membership.version))

        users = await identified_users(db, [entity_key])
        membership = await dao_memberships.set_status(
            db, membership, data.status, now, commit=False
        )
        state = MemberResponse(
            user_id=entity_key,
            display_name=users[entity_key].display_name,
            role="assistant",
            status=membership.status,
            created_at=membership.created_at,
            updated_at=membership.updated_at,
            version=membership.version,
        )

        return Ok(
            AccountEffect(
                state,
                state.version,
                [AccountChange("membership", str(entity_key), state, state.version)],
                True,
            )
        )

    if action == "CreateInvitation":
        if not isinstance(payload, CreateInvitationPayload):
            return Err(AccountRuleError("VALIDATION_ERROR"))

        data = payload
        existing = await dao_invitations.get(db, entity_key)

        if existing is not Empty and existing.account_id != context.account.id:
            return Err(AccountObjectNotFound())

        if expected_version != 0 or existing is not Empty:
            return Err(
                AccountRuleError(
                    "VERSION_CONFLICT", None if existing is Empty else existing.version
                )
            )

        users = await identified_users(db, [data.invitee_user_id])

        if data.invitee_user_id not in users:
            return Err(AccountObjectNotFound())

        if data.invitee_user_id == context.account.owner_user_id:
            return Err(AccountRuleError("NO_CHANGES"))

        invitation = await dao_invitations.create(
            db,
            commit=False,
            obj_in={
                "id": entity_key,
                "account_id": context.account.id,
                "invitee_user_id": data.invitee_user_id,
                "created_by_user_id": context.actor.user_id,
                "created_at": now,
                "updated_at": now,
                "expires_at": now + timedelta(hours=72),
                "accepted_at": None,
                "accepted_operation_id": None,
            },
        )
        state = invitation_view(invitation, now)

        return Ok(
            AccountEffect(
                state,
                state.version,
                [AccountChange("invitation", str(entity_key), state, state.version)],
                False,
            )
        )

    invitation = await dao_invitations.get_scoped(db, entity_key, context.account.id)

    if invitation is Empty or (
        action == "AcceptInvitation"
        and invitation.invitee_user_id != context.actor.user_id
    ):
        return Err(AccountObjectNotFound())

    if action == "RevokeInvitation" and invitation.version != expected_version:
        return Err(AccountRuleError("VERSION_CONFLICT", invitation.version))

    if invitation.status != "pending" or invitation.expires_at <= now:
        return Err(AccountRuleError("INVALID_STATE_TRANSITION", invitation.version))

    if action == "RevokeInvitation":
        invitation = await dao_invitations.resolve(db, invitation, now, commit=False)
        state = invitation_view(invitation, now)

        return Ok(
            AccountEffect(
                state,
                state.version,
                [AccountChange("invitation", str(entity_key), state, state.version)],
                False,
            )
        )

    membership = await dao_memberships.get_scoped(
        db, context.account.id, context.actor.user_id
    )

    if membership is not Empty and membership.status == "active":
        return Err(AccountRuleError("NO_CHANGES", membership.version))

    if membership is Empty:
        membership = await dao_memberships.create_membership(
            db, context.account.id, context.actor.user_id, now, commit=False
        )
    else:
        membership = await dao_memberships.set_status(
            db, membership, "active", now, commit=False
        )

    users = await identified_users(db, [context.actor.user_id])
    member = MemberResponse(
        user_id=context.actor.user_id,
        display_name=users[context.actor.user_id].display_name,
        role="assistant",
        status="active",
        created_at=membership.created_at,
        updated_at=membership.updated_at,
        version=membership.version,
    )
    invitation = await dao_invitations.resolve(
        db, invitation, now, accepted_operation_id=operation_id, commit=False
    )
    state = InvitationAcceptanceResult(
        operation_id=operation_id,
        status="accepted",
        invitation_id=entity_key,
        account_id=context.account.id,
        membership_version=membership.version,
    )

    return Ok(
        AccountEffect(
            state,
            membership.version,
            [
                AccountChange(
                    "invitation",
                    str(entity_key),
                    invitation_view(invitation, now),
                    invitation.version,
                ),
                AccountChange(
                    "membership", str(context.actor.user_id), member, member.version
                ),
            ],
            True,
        )
    )


async def get_invitations(
    db: AsyncSession,
    credential: str | None,
    query: InvitationQuery,
    account_id: UUID | None = None,
):
    from src.api.accounts.application.accounts_cases import account_context

    async with transaction(db):
        identity = await authenticate(db, credential)

        if isinstance(identity, Err):
            return identity

        actor = identity.value

        if account_id is not None:
            scope = await account_context(db, actor, account_id, require_device=True)

            if isinstance(scope, Err):
                return scope

            if not scope.value.owner or scope.value.account.status != "active":
                return Err(AccessDenied())

        now = await dao_accounts.get_server_time(db)
        rows, total = await dao_invitations.page(
            db,
            now,
            account_id=account_id,
            user_id=actor.user_id if account_id is None else None,
            status=query.status,
            offset=(query.page - 1) * query.shows,
            shows=query.shows,
        )
        response = PaginatedResponse[InvitationResponse](
            items=[invitation_view(row, now) for row in rows], total=total
        )

    return Ok(response)
