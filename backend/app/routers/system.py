from fastapi import APIRouter

from app.schemas.system import PingResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/ping", response_model=PingResponse)
async def ping() -> PingResponse:
    return PingResponse()
