from typing import assert_never

from fastapi import APIRouter, Depends

from src.api.errors import no_query_parameters
from src.api.sync.application.capabilities_cases import get_capabilities
from src.api.sync.domain.capabilities import CapabilitiesResponse
from src.core import Ok
from src.core.schema import ApiError

router = APIRouter(prefix="/v1", tags=["sync"], responses={422: {"model": ApiError}})


@router.get(
    "/capabilities",
    operation_id="getCapabilities",
    response_model=CapabilitiesResponse,
    dependencies=[Depends(no_query_parameters)],
)
async def capabilities() -> CapabilitiesResponse:
    match get_capabilities():
        case Ok(response):
            return response
        case unexpected:
            assert_never(unexpected)
