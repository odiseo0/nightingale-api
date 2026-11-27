from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, assert_never
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.billing.application.patient_cases import GrantNotUsable
from src.api.billing.application.report_cases import (
    PatientReportDetail,
    PatientReportSubmit,
    PatientReportView,
    ReportNotFound,
    ReportRejected,
    list_own_reports,
    read_own_report,
    submit_report,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, BaseModel

router = APIRouter(
    tags=["patient-billing"],
    responses={code: {"model": ApiError} for code in (404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


class PatientReportPage(BaseModel):
    items: list[PatientReportView]
    total: int


def _secret(authorization: HTTPAuthorizationCredentials | None) -> str | None:
    return authorization.credentials if authorization else None


@router.post(
    "/v1/patient/billing/reports",
    operation_id="submitPatientPaymentReport",
    response_model=PatientReportView,
    status_code=201,
)
async def submit_patient_payment_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    operation_id: Annotated[UUID, Form(alias="operationId")],
    charge_id: Annotated[UUID, Form(alias="chargeId")],
    paid_on: Annotated[date, Form(alias="paidOn")],
    amount: Annotated[Decimal, Form()],
    currency: Annotated[Literal["USD", "VES"], Form()],
    method: Annotated[str, Form()],
    capture: Annotated[UploadFile, File()],
    reference_last4: Annotated[str | None, Form(alias="referenceLast4")] = None,
    note: Annotated[str | None, Form()] = None,
    previous_report_id: Annotated[UUID | None, Form(alias="previousReportId")] = None,
) -> PatientReportView:
    data = PatientReportSubmit(
        operation_id=operation_id,
        charge_id=charge_id,
        paid_on=paid_on,
        amount=amount,
        currency=currency,
        method=method,
        reference_last4=reference_last4,
        note=note,
        previous_report_id=previous_report_id,
    )
    result = await submit_report(db, _secret(authorization), data, await capture.read())

    match result:
        case Ok(response):
            return response
        case Err(GrantNotUsable() | ReportNotFound()):
            # Invalid links and out-of-scope charges never confirm existence.
            raise HTTPException(404)
        case Err(ReportRejected(reason=reason)):
            raise HTTPException(422, detail=reason)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/v1/patient/billing/reports",
    operation_id="listPatientPaymentReports",
    response_model=PatientReportPage,
)
async def list_patient_payment_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, object]:
    result = await list_own_reports(db, _secret(authorization))

    match result:
        case Ok(response):
            return response
        case Err(GrantNotUsable()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/v1/patient/billing/reports/{report_id}",
    operation_id="readPatientPaymentReport",
    response_model=PatientReportDetail,
)
async def read_patient_payment_report(
    report_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PatientReportDetail:
    result = await read_own_report(db, _secret(authorization), report_id)

    match result:
        case Ok(response):
            return response
        case Err(GrantNotUsable() | ReportNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)
