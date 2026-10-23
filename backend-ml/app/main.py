import logging
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import system
from app.services.model import model_lifespan
from app.shared.config import settings
from app.shared.logging import init_app_logging

logger = logging.getLogger(__name__)


init_app_logging()

logger.info(
    f"[STARTUP] Loaded CORS Origins (Type: {type(settings.CORS_ORIGINS)}): {settings.CORS_ORIGINS}"
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[dict[str, Any], None]:
    async with AsyncExitStack() as stack:
        state: dict[str, Any] = {}

        for sub_lifespan in (
            model_lifespan(
                model_path=settings.MODEL_PATH,
                thread_count=settings.MODEL_THREAD_COUNT,
            ),
        ):
            state |= await stack.enter_async_context(sub_lifespan)

        yield state


app = FastAPI(
    title="AlfaHack ML",
    lifespan=lifespan,
    version="0.1.0",
    docs_url="/docs" if settings.DEV else None,
    redoc_url="/redoc" if settings.DEV else None,
    openapi_url="/openapi.json" if settings.DEV else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Accept-Ranges"],
)

router = APIRouter(prefix="/api")
router.include_router(system.router)

app.include_router(router)
