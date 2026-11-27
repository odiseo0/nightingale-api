from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.billing.application.charge_cases import billing_scope
from src.api.billing.application.review_cases import (
    ApprovalResult,
    BillingApprovalRequest,
    BillingRejectionRequest,
    PaymentExceedsBalanceError,
    ReportNotPendingError,
    ReviewDetail,
    ReviewItem,
    approve_report,
    reject_report,
    review_detail,
    review_evidence,
    review_inbox,
)
from src.api.billing.domain.payments import CurrencyMismatchError
from src.core import Err, Ok
from src.core.db import get_db, transaction
from src.core.schema import ApiError, BaseModel, PageQuery, PaginatedResponse

router = APIRouter(
    tags=["billing"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


class ReviewPage(BaseModel):
    items: list[ReviewItem]
    total: int


@router.get(
    "/v1/accounts/{account_id}/billing/reports",
    operation_id="listBillingReports",
    response_model=PaginatedResponse[ReviewItem],
)
async def list_billing_reports(
    account_id: UUID7,
    query: Annotated[PageQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    status: Annotated[str | None, Query()] = "pending",
    charge_id: Annotated[UUID7 | None, Query(alias="chargeId")] = None,
    patient_id: Annotated[UUID7 | None, Query(alias="patientId")] = None,
) -> dict[str, object]:
    async with transaction(db):
        scope = await billing_scope(
            db, authorization.credentials if authorization else None,
            account_id, "billing_review",
        )

        if isinstance(scope, Err):
            result = scope
        else:
            result = Ok(
                await review_inbox(
                    db, account_id, query.page, query.shows,
                    status=status, charge_id=charge_id, patient_id=patient_id,
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


@router.get(
    "/v1/accounts/{account_id}/billing/reports/{report_id}",
    operation_id="getBillingReport",
    response_model=ReviewDetail,
)
async def get_billing_report(
    account_id: UUID7,
    report_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ReviewDetail:
    async with transaction(db):
        scope = await billing_scope(
            db, authorization.credentials if authorization else None,
            account_id, "billing_review",
        )

        if isinstance(scope, Err):
            result = scope
        else:
            result = await review_detail(db, account_id, report_id)

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get(
    "/v1/accounts/{account_id}/billing/reports/{report_id}/evidence",
    operation_id="downloadBillingReportEvidence",
)
async def download_billing_report_evidence(
    account_id: UUID7,
    report_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Response:
    async with transaction(db):
        scope = await billing_scope(
            db, authorization.credentials if authorization else None,
            account_id, "billing_review",
        )

        if isinstance(scope, Err):
            result = scope
        else:
            result = await review_evidence(db, account_id, report_id)

    match result:
        case Ok((content_type, content)):
            # Generated internal name; never the storage key nor a public URL.
            return Response(
                content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="evidence-{report_id}"'
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


@router.post(
    "/v1/accounts/{account_id}/billing/reports/{report_id}/approval",
    operation_id="approveBillingReport",
    response_model=ApprovalResult,
)
async def approve_billing_report(
    account_id: UUID7,
    report_id: UUID7,
    payload: BillingApprovalRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ApprovalResult:
    async with transaction(db):
        scope = await billing_scope(
            db, authorization.credentials if authorization else None,
            account_id, "billing_review",
        )

        if isinstance(scope, Err):
            result = scope
        else:
            result = await approve_report(db, scope.value, report_id, payload)

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case Err(ReportNotPendingError()):
            raise HTTPException(409, detail="REPORT_NOT_PENDING")
        case Err(PaymentExceedsBalanceError()):
            raise HTTPException(422, detail="PAYMENT_EXCEEDS_BALANCE")
        case Err(CurrencyMismatchError()):
            raise HTTPException(422, detail="PAYMENT_MISMATCH")
        case unexpected:
            assert_never(unexpected)


@router.post(
    "/v1/accounts/{account_id}/billing/reports/{report_id}/rejection",
    operation_id="rejectBillingReport",
    response_model=ReviewItem,
)
async def reject_billing_report(
    account_id: UUID7,
    report_id: UUID7,
    payload: BillingRejectionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ReviewItem:
    async with transaction(db):
        scope = await billing_scope(
            db, authorization.credentials if authorization else None,
            account_id, "billing_review",
        )

        if isinstance(scope, Err):
            result = scope
        else:
            result = await reject_report(db, scope.value, report_id, payload)

    match result:
        case Ok(response):
            return response
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case Err(ReportNotPendingError()):
            raise HTTPException(409, detail="REPORT_NOT_PENDING")
        case unexpected:
            assert_never(unexpected)
