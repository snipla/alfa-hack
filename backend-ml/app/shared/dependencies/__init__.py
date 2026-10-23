from typing import Annotated

from app.services.model import CatBoostModelService
from app.shared.dependencies.auth import (
    OptionalAuth,
    RequireAuth,
    optional_auth,
    require_auth,
)
from fastapi import Depends, Request


def get_model_service(request: Request) -> CatBoostModelService:
    return request.app.state.model_service


ModelService = Annotated[CatBoostModelService, Depends(get_model_service)]

__all__ = [
    "ModelService",
    "OptionalAuth",
    "RequireAuth",
    "get_model_service",
    "optional_auth",
    "require_auth",
]
