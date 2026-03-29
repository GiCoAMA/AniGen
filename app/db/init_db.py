"""One-shot database bootstrap (default admin user, etc.)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User

_DEFAULT_ADMIN_USERNAME = "anigen_admin"
_DEFAULT_ADMIN_PASSWORD = "AniGen_Admin_9xK2!"


async def init_db(session: AsyncSession) -> None:
    """Ensure built-in records exist (idempotent)."""

    result = await session.execute(
        select(User).where(User.username == _DEFAULT_ADMIN_USERNAME)
    )
    if result.scalar_one_or_none() is not None:
        return

    session.add(
        User(
            username=_DEFAULT_ADMIN_USERNAME,
            hashed_password=get_password_hash(_DEFAULT_ADMIN_PASSWORD),
            is_active=True,
        )
    )
    await session.commit()
