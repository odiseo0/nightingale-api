from typing import Annotated, assert_never
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.billing.application.patient_cases import (
    read_patient_charges,
    read_patient_receipt,
)
from src.api.billing.domain.payments import PatientChargeView
from src.core import Err, Ok
from src.core.db import get_db, transaction
from src.core.schema import ApiError, BaseModel

router = APIRouter(
    tags=["patient-billing"],
    responses={code: {"model": ApiError} for code in (404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


class PatientChargePage(BaseModel):
    items: list[PatientChargeView]
    total: int


@router.get(
    "/v1/patient/billing/charge",
    operation_id="readPatientBillingCharge",
    response_model=PatientChargePage,
)
async def read_patient_billing_charge(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    async with db.begin():
        result = await read_patient_charges(
            db, authorization.credentials if authorization else None
        )

    match result:
        case Ok(response):
            return response
        case Err(_):
            # Expired, revoked, foreign or action-less links are a uniform 404:
            # they never confirm that the object exists (D28).
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/v1/patient/billing/payments/{payment_id}/receipt",
    operation_id="readPatientPaymentReceipt",
)
async def read_patient_payment_receipt(
    payment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Response:
    async with transaction(db):
        result = await read_patient_receipt(
            db, authorization.credentials if authorization else None, payment_id
        )

    match result:
        case Ok((content_type, content)):
            return Response(
                content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="receipt-{payment_id}.pdf"'
                },
            )
        case Err(_):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)
