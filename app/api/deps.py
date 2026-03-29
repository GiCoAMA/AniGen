from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Query, Request, WebSocket, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status as starlette_status
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")

# Atomic INCR + set TTL on first hit in the window (fixed window per key).
_RATE_LIMIT_INCR_EXPIRE_LUA = """
local c = redis.call('INCR', KEYS[1])
if c == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return c
"""


async def user_from_access_token(session: AsyncSession, token: str) -> User:
    """Load user from JWT access token; raise ``ValueError`` if invalid or inactive."""

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        sub = payload.get("sub")
        if sub is None:
            raise ValueError("Invalid token")
        user_id = int(sub)
    except (InvalidTokenError, ValueError, TypeError) as exc:
        raise ValueError("Could not validate credentials") from exc

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise ValueError("User not found or inactive")
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the current user from the Bearer JWT (OpenAPI OAuth2 password flow)."""

    try:
        return await user_from_access_token(db, token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user_ws(
    websocket: WebSocket,
    token: Annotated[
        str,
        Query(..., description="JWT from query string (browser WebSocket has no custom headers)."),
    ],
    session: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate WebSocket clients via ``?token=`` before the route calls ``accept()``."""

    try:
        return await user_from_access_token(session, token)
    except ValueError:
        await websocket.close(
            code=starlette_status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired token",
        )
        raise WebSocketDisconnect(
            code=starlette_status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired token",
        ) from None


class RateLimiter:
    """Redis-backed fixed-window rate limiter (per user), for use as ``Depends(...)``."""

    def __init__(
        self,
        times: int,
        seconds: int,
        *,
        key_suffix: str = "generate",
    ) -> None:
        if times < 1 or seconds < 1:
            raise ValueError("times and seconds must be positive")
        self.times = times
        self.seconds = seconds
        self.key_suffix = key_suffix

    async def __call__(
        self,
        request: Request,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> None:
        redis = request.app.state.redis
        key = f"rate_limit:user:{current_user.id}:{self.key_suffix}"
        count_raw = await redis.eval(
            _RATE_LIMIT_INCR_EXPIRE_LUA,
            1,
            key,
            str(self.seconds),
        )
        count = int(count_raw)
        if count > self.times:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests in this time window",
                headers={"Retry-After": str(self.seconds)},
            )
