from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.billing.application.charge_cases import (
    billing_scope,
    read_charge_detail,
    read_charges,
)
from src.api.billing.application.grant_cases import (
    issue_grant,
    list_grants,
    revoke_grant,
)
from src.api.billing.domain.charges import ChargeResponse
from src.api.billing.domain.payments import (
    GrantCreateRequest,
    GrantIssuedResponse,
    GrantResponse,
)
from src.core import Err, Ok
from src.core.db import get_db, transaction
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    tags=["billing"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.get(
    "/v1/accounts/{account_id}/billing/charges",
    operation_id="listBillingCharges",
    response_model=PaginatedResponse[ChargeResponse],
)
async def list_billing_charges(
    account_id: UUID7,
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    patient_id: Annotated[UUID7 | None, Query(alias="patientId")] = None,
    status: Annotated[str | None, Query()] = None,
) -> dict[str, object]:
    result = await read_charges(
        db,
        authorization.credentials if authorization else None,
        account_id,
        query.page,
        query.shows,
        patient_id=patient_id,
        status=status,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/v1/accounts/{account_id}/billing/charges/{charge_id}",
    operation_id="getBillingCharge",
    response_model=ChargeResponse,
)
async def get_billing_charge(
    account_id: UUID7,
    charge_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ChargeResponse:
    result = await read_charge_detail(
        db, authorization.credentials if authorization else None, account_id, charge_id
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/v1/accounts/{account_id}/billing/grants",
    operation_id="issueBillingGrant",
    response_model=GrantIssuedResponse,
    status_code=201,
)
async def issue_billing_grant(
    account_id: UUID7,
    payload: GrantCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> GrantIssuedResponse:
    async with transaction(db):
        scope = await billing_scope(
            db,
            authorization.credentials if authorization else None,
            account_id,
            "billing_review",
        )

        if isinstance(scope, Err):
            result = scope
        else:
            result = await issue_grant(db, scope.value, payload)

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied() | AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case Err(AccountRuleError()):
            raise HTTPException(422)
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/v1/accounts/{account_id}/billing/grants/{grant_id}/revocation",
    operation_id="revokeBillingGrant",
    response_model=GrantResponse,
)
async def revoke_billing_grant(
    account_id: UUID7,
    grant_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> GrantResponse:
    async with transaction(db):
        scope = await billing_scope(
            db,
            authorization.credentials if authorization else None,
            account_id,
            "billing_review",
        )

        if isinstance(scope, Err):
            result = scope
        else:
            result = await revoke_grant(db, scope.value, grant_id)

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied() | AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/v1/accounts/{account_id}/billing/grants",
    operation_id="listBillingGrants",
    response_model=PaginatedResponse[GrantResponse],
)
async def list_billing_grants(
    account_id: UUID7,
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    patient_id: Annotated[UUID7 | None, Query(alias="patientId")] = None,
    charge_id: Annotated[UUID7 | None, Query(alias="chargeId")] = None,
) -> dict[str, object]:
    async with transaction(db):
        scope = await billing_scope(
            db, authorization.credentials if authorization else None, account_id
        )

        if isinstance(scope, Err):
            result = scope
        else:
            result = Ok(
                await list_grants(
                    db,
                    account_id,
                    query.page,
                    query.shows,
                    patient_id=patient_id,
                    charge_id=charge_id,
                )
            )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)
