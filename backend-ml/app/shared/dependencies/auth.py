import hashlib
import hmac
from typing import Annotated

from app.shared.config import settings
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(
    scheme_name="Bearer API Key",
    description="Enter API_KEY (ex: sk_...)",
)
optional_bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="Bearer API Key",
    description="Enter API_KEY (ex: sk_...)",
)

_SALT_BYTES: bytes = settings.API_KEY_SALT.get_secret_value().encode("utf-8")
_EXPECTED_HASH: str = settings.SYSTEM_API_KEY_HASH.get_secret_value()


def _verify_api_key(raw_key: str) -> bool:
    computed_hash = hmac.new(
        _SALT_BYTES,
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed_hash, _EXPECTED_HASH)


async def _resolve_credentials(raw_token: str) -> bool:
    if not _verify_api_key(raw_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


def _extract_raw_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    return None


BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(optional_bearer_scheme)
]


async def require_auth(
    request: Request,
    credentials: BearerCredentials = None,
) -> bool:
    raw_token = _extract_raw_token(credentials)

    if not raw_token:
        request.state.is_authenticated = False
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await _resolve_credentials(raw_token)
    request.state.is_authenticated = True
    return True


async def optional_auth(
    request: Request,
    credentials: BearerCredentials = None,
) -> bool:
    raw_token = _extract_raw_token(credentials)

    if not raw_token:
        request.state.is_authenticated = False
        return False

    try:
        await _resolve_credentials(raw_token)
    except HTTPException:
        request.state.is_authenticated = False
        return False

    request.state.is_authenticated = True
    return True


RequireAuth = Annotated[bool, Depends(require_auth)]
OptionalAuth = Annotated[bool, Depends(optional_auth)]
