from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from arq import create_pool
from arq.connections import RedisSettings

from app.api.v1.endpoints.images import router as images_router
from app.core.config import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_STATIC_ROOT = _PROJECT_ROOT / "static"
_STATIC_IMAGES = _STATIC_ROOT / "images"
_DATA_DIR = _PROJECT_ROOT / "data"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    _STATIC_IMAGES.mkdir(parents=True, exist_ok=True)
    _DATA_DIR.mkdir(parents=True, exist_ok=True)

    app.state.redis = await create_pool(
        RedisSettings(host=settings.redis_host, port=settings.redis_port)
    )
    try:
        yield
    finally:
        redis = getattr(app.state, "redis", None)
        if redis is not None:
            await redis.close()


app: FastAPI = FastAPI(title=settings.app_title, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(images_router, prefix="/api/v1")
app.mount(
    "/static",
    StaticFiles(directory=str(_STATIC_ROOT)),
    name="static",
)
