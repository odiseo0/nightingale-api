from fastapi import APIRouter

router = APIRouter(prefix="/health", include_in_schema=False)


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "alive"}
