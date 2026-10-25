from fastapi import APIRouter

from app.domains.system.schemas import PingResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/ping", response_model=PingResponse)
async def ping() -> PingResponse:
    return PingResponse()
