from typing import Annotated, Literal, assert_never
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.evidence_cases import (
    EvidenceNotFound,
    ReportNotFound,
)
from src.api.subscriptions.application.review_cases import (
    PaymentMismatch,
    RateMismatch,
    ReportNotPending,
    VersionConflict,
    approve_report,
    list_reports_for_operator,
    read_evidence_for_operator,
    reject_report,
    report_detail_for_operator,
)
from src.api.subscriptions.domain.reports import (
    OperatorPaymentReportDetail,
    OperatorPaymentReportPage,
)
from src.api.subscriptions.domain.reviews import (
    ApprovalRequest,
    ApprovalResultResponse,
    RejectionRequest,
    RejectionResultResponse,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery

router = APIRouter(
    prefix="/v1/operator/payment-reports",
    tags=["operator-subscriptions"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422)},
)
bearer = HTTPBearer(auto_error=False)


@router.get("", operation_id="listOperatorPaymentReports")
async def list_operator_payment_reports(
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    status: Annotated[
        Literal["pending", "approved", "rejected"] | None, Query()
    ] = None,
    account_id: Annotated[UUID | None, Query(alias="accountId")] = None,
) -> OperatorPaymentReportPage:
    result = await list_reports_for_operator(
        db,
        authorization.credentials if authorization else None,
        status,
        account_id,
        query.page,
        query.shows,
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case unexpected:
            assert_never(unexpected)


@router.post("/{report_id}/approval", operation_id="approveOperatorPaymentReport")
async def approve_operator_payment_report(
    report_id: UUID7,
    payload: ApprovalRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ApprovalResultResponse:
    result = await approve_report(
        db, authorization.credentials if authorization else None, report_id, payload
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(ReportNotFound()):
            raise HTTPException(404)
        case Err(ReportNotPending()):
            raise HTTPException(409, detail="REPORT_NOT_PENDING")
        case Err(VersionConflict()):
            raise HTTPException(409, detail="VERSION_CONFLICT")
        case Err(PaymentMismatch()):
            raise HTTPException(422, detail="PAYMENT_MISMATCH")
        case Err(RateMismatch()):
            raise HTTPException(422, detail="RATE_MISMATCH")
        case unexpected:
            assert_never(unexpected)


@router.post("/{report_id}/rejection", operation_id="rejectOperatorPaymentReport")
async def reject_operator_payment_report(
    report_id: UUID7,
    payload: RejectionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> RejectionResultResponse:
    result = await reject_report(
        db, authorization.credentials if authorization else None, report_id, payload
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(ReportNotFound()):
            raise HTTPException(404)
        case Err(ReportNotPending()):
            raise HTTPException(409, detail="REPORT_NOT_PENDING")
        case Err(VersionConflict()):
            raise HTTPException(409, detail="VERSION_CONFLICT")
        case unexpected:
            assert_never(unexpected)


@router.get("/{report_id}", operation_id="getOperatorPaymentReport")
async def get_operator_payment_report(
    report_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> OperatorPaymentReportDetail:
    result = await report_detail_for_operator(
        db, authorization.credentials if authorization else None, report_id
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(ReportNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/{report_id}/evidence", operation_id="downloadOperatorPaymentReportEvidence"
)
async def download_operator_payment_report_evidence(
    report_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Response:
    result = await read_evidence_for_operator(
        db, authorization.credentials if authorization else None, report_id
    )

    match result:
        case Ok((content_type, content)):
            return Response(
                content=content,
                media_type=content_type,
                headers={"Cache-Control": "no-store"},
            )
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(ReportNotFound() | EvidenceNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)
