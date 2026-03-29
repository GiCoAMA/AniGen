import base64
import binascii
import json
import logging
from typing import Any, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import get_storage
from app.db.database import SessionLocal
from app.models.task import ImageTask
from app.schemas.image import TaskStatus

logger = logging.getLogger(__name__)

STATUS_PENDING: TaskStatus = "PENDING"
STATUS_COMPLETED: TaskStatus = "COMPLETED"
STATUS_FAILED: TaskStatus = "FAILED"

SD_REQUEST_TIMEOUT_SECONDS = 60.0
SD_TXT2IMG_PATH = "/sdapi/v1/txt2img"


def _sd_txt2img_url() -> str:
    base = str(settings.sd_webui_url).rstrip("/")
    return f"{base}{SD_TXT2IMG_PATH}"


async def create_image_task(
    session: AsyncSession,
    task_id: UUID,
    prompt: str,
    *,
    user_id: int,
    width: int,
    height: int,
    steps: int,
) -> None:
    """Insert a new task row into the database.

    ``width`` / ``height`` / ``steps`` are accepted for API symmetry; the worker
    receives them via the ARQ job payload (see ``enqueue_job`` at the call site).
    """

    session.add(
        ImageTask(
            id=str(task_id),
            prompt=prompt,
            status=STATUS_PENDING,
            image_url=None,
            user_id=user_id,
        )
    )
    await session.commit()


async def get_task_status(session: AsyncSession, task_id: UUID) -> Optional[TaskStatus]:
    """Fetch the current status for a task."""

    result = await session.execute(
        select(ImageTask.status).where(ImageTask.id == str(task_id))
    )
    return result.scalar_one_or_none()



async def get_task_status_image_url_for_access_check(
    session: AsyncSession,
    task_id: UUID,
) -> Optional[tuple[TaskStatus, Optional[str], Optional[int]]]:
    """Return status, image_url, user_id for a task, or None if task does not exist."""

    result = await session.execute(
        select(ImageTask.status, ImageTask.image_url, ImageTask.user_id).where(
            ImageTask.id == str(task_id)
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    return row[0], row[1], row[2]


async def get_task_status_and_image_url(
    session: AsyncSession,
    task_id: UUID,
    *,
    user_id: int,
) -> Optional[tuple[TaskStatus, Optional[str]]]:
    """Fetch status and image_url for task detail responses."""

    result = await session.execute(
        select(ImageTask.status, ImageTask.image_url).where(
            ImageTask.id == str(task_id),
            ImageTask.user_id == user_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    return row[0], row[1]


async def _update_task(
    task_uuid: UUID,
    *,
    status: TaskStatus,
    image_url: Optional[str] = None,
) -> None:
    values: dict[str, Any] = {"status": status}
    if image_url is not None:
        values["image_url"] = image_url
    async with SessionLocal() as session:
        await session.execute(
            update(ImageTask).where(ImageTask.id == str(task_uuid)).values(**values)
        )
        await session.commit()


async def generate_image_task(
    ctx: dict[str, Any],
    task_id: str,
    width: int = 512,
    height: int = 512,
    steps: int = 20,
) -> None:
    """Call SD WebUI txt2img, persist bytes via ``get_storage().save_image``, update DB."""

    _ = ctx
    task_uuid = UUID(task_id)

    async with SessionLocal() as session:
        result = await session.execute(
            select(ImageTask.prompt).where(ImageTask.id == str(task_uuid))
        )
        prompt = result.scalar_one_or_none()

    if prompt is None:
        logger.warning("ImageTask not found for task_id=%s", task_id)
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    txt2img_url = _sd_txt2img_url()
    payload = {
        "prompt": prompt,
        "steps": steps,
        "width": width,
        "height": height,
    }
    try:
        timeout = httpx.Timeout(SD_REQUEST_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(
                "SD WebUI txt2img POST task_id=%s url=%s",
                task_id,
                txt2img_url,
            )
            response = await client.post(txt2img_url, json=payload)
    except (httpx.TimeoutException, httpx.RequestError):
        logger.exception("SD API request failed for task_id=%s", task_id)
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    if not response.is_success:
        logger.error(
            "SD API returned error status=%s task_id=%s body=%s",
            response.status_code,
            task_id,
            response.text[:500],
        )
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    try:
        body = response.json()
    except json.JSONDecodeError:
        logger.exception(
            "SD API returned non-JSON body for task_id=%s snippet=%s",
            task_id,
            response.text[:200],
        )
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    if not isinstance(body, dict):
        logger.error("SD API JSON root is not an object task_id=%s", task_id)
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    images = body.get("images")
    if not isinstance(images, list) or len(images) < 1:
        logger.error(
            "SD API missing or empty images[] task_id=%s keys=%s",
            task_id,
            list(body.keys()) if isinstance(body, dict) else None,
        )
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    b64_payload = images[0]
    if not isinstance(b64_payload, str) or not b64_payload.strip():
        logger.error("SD API images[0] is not a non-empty string task_id=%s", task_id)
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    try:
        raw_png = base64.b64decode(b64_payload, validate=False)
    except binascii.Error:
        logger.exception("Failed to base64-decode SD image for task_id=%s", task_id)
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    if not raw_png:
        logger.error("Decoded image is empty task_id=%s", task_id)
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    image_bytes = raw_png
    try:
        storage = get_storage()
    except (NotImplementedError, ValueError):
        logger.exception(
            "Storage backend unavailable or invalid for task_id=%s (storage_backend=%r)",
            task_id,
            settings.storage_backend,
        )
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    try:
        image_url = await storage.save_image(task_id, image_bytes)
    except OSError:
        logger.exception("Failed to save image for task_id=%s", task_id)
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    await _update_task(
        task_uuid,
        status=STATUS_COMPLETED,
        image_url=image_url,
    )
