from typing import Annotated, Literal, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.subscriptions.application.evidence_cases import (
    EvidenceAlreadyPresent,
    EvidenceNotFound,
    EvidenceRejected,
    ReportNotFound,
    ReportNotPending,
    read_evidence,
    upload_evidence,
)
from src.api.subscriptions.application.report_cases import (
    IdempotencyConflict,
    PlanUnavailable,
    list_reports,
    report_detail,
    submit_report,
)
from src.api.subscriptions.domain.reports import (
    PaymentReportCreateRequest,
    PaymentReportDetailResponse,
    PaymentReportResponse,
)
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/subscription/reports",
    tags=["subscriptions"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 409, 422)},
)
bearer = HTTPBearer(auto_error=False)


@router.post("", operation_id="submitPaymentReport", status_code=201)
async def submit_payment_report(
    account_id: UUID7,
    payload: PaymentReportCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaymentReportResponse:
    result = await submit_report(
        db, authorization.credentials if authorization else None, account_id, payload
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
        case Err(PlanUnavailable()):
            raise HTTPException(409, detail="PLAN_UNAVAILABLE")
        case Err(IdempotencyConflict()):
            raise HTTPException(409, detail="IDEMPOTENCY_CONFLICT")
        case unexpected:
            assert_never(unexpected)


@router.get("", operation_id="listPaymentReports")
async def list_payment_reports(
    account_id: UUID7,
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    status: Annotated[
        Literal["pending", "approved", "rejected"] | None, Query()
    ] = None,
) -> PaginatedResponse[PaymentReportResponse]:
    result = await list_reports(
        db,
        authorization.credentials if authorization else None,
        account_id,
        status,
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
        case Err(AccountNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get("/{report_id}", operation_id="getPaymentReport")
async def get_payment_report(
    account_id: UUID7,
    report_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaymentReportDetailResponse:
    result = await report_detail(
        db, authorization.credentials if authorization else None, account_id, report_id
    )

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | ReportNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/{report_id}/evidence", operation_id="uploadPaymentReportEvidence", status_code=201
)
async def upload_payment_report_evidence(
    account_id: UUID7,
    report_id: UUID7,
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Response:
    from src.api.subscriptions.domain.reports import EVIDENCE_MAX_BYTES

    content = await file.read(EVIDENCE_MAX_BYTES + 1)
    result = await upload_evidence(
        db,
        authorization.credentials if authorization else None,
        account_id,
        report_id,
        content,
    )

    match result:
        case Ok(_):
            return Response(status_code=201)
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | ReportNotFound()):
            raise HTTPException(404)
        case Err(ReportNotPending()):
            raise HTTPException(409, detail="INVALID_STATE_TRANSITION")
        case Err(EvidenceAlreadyPresent()):
            raise HTTPException(409, detail="EVIDENCE_ALREADY_PRESENT")
        case Err(EvidenceRejected(reason)):
            raise HTTPException(422, detail=reason)
        case unexpected:
            assert_never(unexpected)


@router.get("/{report_id}/evidence", operation_id="downloadPaymentReportEvidence")
async def download_payment_report_evidence(
    account_id: UUID7,
    report_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Response:
    context_result = await read_evidence_authorized(
        db, authorization, account_id, report_id
    )

    match context_result:
        case Ok((content_type, content)):
            return Response(
                content=content,
                media_type=content_type,
                headers={"Cache-Control": "no-store"},
            )
        case Err(error):
            raise error
        case unexpected:
            assert_never(unexpected)


async def read_evidence_authorized(db, authorization, account_id, report_id):
    from src.api.accounts.application.accounts_cases import get_account_context

    context = await get_account_context(
        db,
        authorization.credentials if authorization else None,
        account_id,
        require_device=True,
    )

    match context:
        case Err(InvalidCredential()):
            return Err(HTTPException(401))
        case Err(AccessDenied()):
            return Err(HTTPException(403))
        case Err(AccountNotFound()):
            return Err(HTTPException(404))
        case Ok(account):
            pass

    if not account.owner:
        return Err(HTTPException(403))

    result = await read_evidence(db, account_id, report_id)

    match result:
        case Ok(found):
            return Ok(found)
        case Err(ReportNotFound() | EvidenceNotFound()):
            return Err(HTTPException(404))
        case unexpected:
            assert_never(unexpected)
