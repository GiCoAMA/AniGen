"""Pluggable image storage (local filesystem, future OSS/S3)."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# Repo root: app/core/storage.py -> parents[2]
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class BaseStorage(ABC):
    """Abstract image sink; implementations return a client-visible URL string."""

    @abstractmethod
    async def save_image(self, task_id: str, image_bytes: bytes) -> str:
        """Persist ``image_bytes`` for ``task_id`` and return its public URL path."""


class LocalStorage(BaseStorage):
    """Write PNG bytes under ``static/images/{task_id}.png``."""

    def __init__(self, images_dir: Path | None = None) -> None:
        self._images_dir = images_dir or (_PROJECT_ROOT / "static" / "images")

    async def save_image(self, task_id: str, image_bytes: bytes) -> str:
        filename = f"{task_id}.png"
        out_path = self._images_dir / filename
        try:
            await asyncio.to_thread(_write_image_file_sync, out_path, image_bytes)
        except OSError:
            logger.exception("Failed to write image task_id=%s path=%s", task_id, out_path)
            raise
        return f"/static/images/{filename}"


def _write_image_file_sync(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def get_storage() -> BaseStorage:
    """Return the active storage implementation from settings."""

    backend = settings.storage_backend.strip().lower()
    if backend == "local":
        return LocalStorage()
    if backend in ("oss", "s3"):
        raise NotImplementedError(
            f"Storage backend {settings.storage_backend!r} is not implemented yet."
        )
    raise ValueError(f"Unknown storage_backend: {settings.storage_backend!r}")
