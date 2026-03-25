from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from arq import create_pool
from arq.connections import RedisSettings

from app.api.v1.endpoints.images import router as images_router
from app.core.config import settings
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure ORM models are registered before create_all.
    from app.models import task  # noqa: F401

    app.state.redis = await create_pool(
        RedisSettings(host=settings.redis_host, port=settings.redis_port)
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        redis = getattr(app.state, "redis", None)
        if redis is not None:
            await redis.close()


app: FastAPI = FastAPI(title=settings.app_title, lifespan=lifespan)
app.include_router(images_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )

