from typing import Annotated, assert_never

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID7
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.accounts.domain.errors import AccountNotFound, AccountObjectNotFound
from src.api.authorization.domain.errors import AccessDenied, InvalidCredential
from src.api.clinical_records.domain.clinical import ClinicalHistoryQuery
from src.api.diagnostic_results.application.report_cases import (
    read_attachment,
    read_report_history,
    read_report_results,
    read_reports,
)
from src.api.diagnostic_results.domain.reports import (
    DiagnosticReportHistoryResponse,
    DiagnosticReportQuery,
    DiagnosticReportResponse,
)
from src.api.diagnostic_results.domain.results import (
    DiagnosticReportResultResponse,
    ReportAttachmentResponse,
)
from src.api.errors import no_query_parameters
from src.core import Err, Ok
from src.core.db import get_db
from src.core.schema import ApiError, PageQuery, PaginatedResponse

router = APIRouter(
    prefix="/v1/accounts/{account_id}/patients/{patient_id}",
    tags=["clinical-diagnostic-reports"],
    responses={code: {"model": ApiError} for code in (401, 403, 404, 422, 503)},
)
bearer = HTTPBearer(auto_error=False)


def _raise(result):
    match result:
        case Ok(value):
            return value
        case Err(InvalidCredential()):
            raise HTTPException(401)
        case Err(AccessDenied()):
            raise HTTPException(403)
        case Err(AccountNotFound() | AccountObjectNotFound()):
            raise HTTPException(404)
        case unexpected:
            assert_never(unexpected)


@router.get("/diagnostic-reports", operation_id="listPatientDiagnosticReports")
async def list_reports(
    account_id: UUID7,
    patient_id: UUID7,
    query: Annotated[DiagnosticReportQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[DiagnosticReportResponse]:
    return _raise(
        await read_reports(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            query,
        )
    )


@router.get(
    "/diagnostic-reports/{report_id}",
    operation_id="getPatientDiagnosticReport",
    dependencies=[Depends(no_query_parameters)],
)
async def get_report(
    account_id: UUID7,
    patient_id: UUID7,
    report_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> DiagnosticReportResponse:
    return _raise(
        await read_reports(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            PageQuery(),
            report_id,
        )
    )


@router.get(
    "/diagnostic-reports/{report_id}/history",
    operation_id="listPatientDiagnosticReportHistory",
)
async def list_report_history(
    account_id: UUID7,
    patient_id: UUID7,
    report_id: UUID7,
    query: Annotated[ClinicalHistoryQuery, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[DiagnosticReportHistoryResponse]:
    return _raise(
        await read_report_history(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            report_id,
            query,
        )
    )


@router.get(
    "/diagnostic-reports/{report_id}/results",
    operation_id="listPatientDiagnosticReportResults",
    dependencies=[Depends(no_query_parameters)],
)
async def list_report_results(
    account_id: UUID7,
    patient_id: UUID7,
    report_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> PaginatedResponse[DiagnosticReportResultResponse]:
    return _raise(
        await read_report_results(
            db,
            authorization.credentials if authorization else None,
            account_id,
            patient_id,
            report_id,
        )
    )


@router.get(
    "/report-attachments/{attachment_id}",
    operation_id="getReportAttachment",
    dependencies=[Depends(no_query_parameters)],
)
async def get_attachment(
    account_id: UUID7,
    patient_id: UUID7,
    attachment_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ReportAttachmentResponse:
    state, _ = _raise(
        await read_attachment(
            db,
            authorization.credentials if authorization else None,
            account_id,
            attachment_id,
        )
    )
    return state


@router.get(
    "/report-attachments/{attachment_id}/content",
    operation_id="downloadReportAttachment",
    dependencies=[Depends(no_query_parameters)],
)
async def download_attachment(
    account_id: UUID7,
    patient_id: UUID7,
    attachment_id: UUID7,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Response:
    state, content = _raise(
        await read_attachment(
            db,
            authorization.credentials if authorization else None,
            account_id,
            attachment_id,
        )
    )
    return Response(
        content=content,
        media_type=state.content_type,
        headers={"Content-Disposition": f'attachment; filename="{state.file_name}"'},
    )
