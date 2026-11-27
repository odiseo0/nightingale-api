from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.billing.application.charge_cases import billing_scope
from src.api.billing.application.correction_cases import (
    PaymentAlreadyAnnulledError,
    PaymentAnnulmentRequest,
    annul_payment,
)
from src.api.billing.application.direct_payment_cases import (
    ChargeNotIssuedError,
    DirectPaymentRequest,
    PaymentResponse,
    register_direct_payment,
)
from src.api.billing.application.receipt_cases import read_receipt
from src.api.billing.application.review_cases import PaymentExceedsBalanceError
from src.api.billing.domain.payments import CurrencyMismatchError
from src.core import Err, Ok
from src.core.db import get_db, transaction
from src.core.schema import ApiError

router = APIRouter(
    tags=["billing"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 409, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


@router.post(
    "/v1/accounts/{account_id}/billing/charges/{charge_id}/payments",
    operation_id="registerDirectPatientPayment",
    response_model=PaymentResponse,
    status_code=201,
)
async def register_direct_patient_payment(
    account_id: UUID7,
    charge_id: UUID7,
    payload: DirectPaymentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaymentResponse:
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
            result = await register_direct_payment(db, scope.value, charge_id, payload)

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case Err(ChargeNotIssuedError()):
            raise HTTPException(409, detail="CHARGE_NOT_ISSUED")
        case Err(PaymentExceedsBalanceError()):
            raise HTTPException(422, detail="PAYMENT_EXCEEDS_BALANCE")
        case Err(CurrencyMismatchError()):
            raise HTTPException(422, detail="PAYMENT_MISMATCH")
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/v1/accounts/{account_id}/billing/payments/{payment_id}/annulment",
    operation_id="annulPatientPayment",
    response_model=PaymentResponse,
)
async def annul_patient_payment(
    account_id: UUID7,
    payment_id: UUID7,
    payload: PaymentAnnulmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaymentResponse:
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
            result = await annul_payment(db, scope.value, payment_id, payload)

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case Err(PaymentAlreadyAnnulledError()):
            raise HTTPException(409, detail="PAYMENT_ALREADY_ANNULLED")
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/v1/accounts/{account_id}/billing/payments/{payment_id}/receipt",
    operation_id="downloadPaymentReceipt",
)
async def download_payment_receipt(
    account_id: UUID7,
    payment_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Response:
    async with transaction(db):
        scope = await billing_scope(
            db, authorization.credentials if authorization else None, account_id
        )

        if isinstance(scope, Err):
            result = scope
        else:
            result = await read_receipt(db, account_id, payment_id)

    match result:
        case Ok((content_type, content)):
            return Response(
                content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="receipt-{payment_id}.pdf"'
                },
            )
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)
