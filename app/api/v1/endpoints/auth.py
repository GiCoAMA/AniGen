from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])
login_router = APIRouter(prefix="/login", tags=["auth"])


async def _login_user_for_token(
    db: AsyncSession,
    username: str,
    password: str,
) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    body: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(
        username=body.username,
        hashed_password=get_password_hash(body.password),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    return {"username": user.username}


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await _login_user_for_token(db, form_data.username, form_data.password)


@login_router.post("/access-token", response_model=TokenResponse)
async def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """OAuth2 password flow: ``application/x-www-form-urlencoded`` body."""
    return await _login_user_for_token(db, form_data.username, form_data.password)
