import logging
from typing import Any, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.task import ImageTask
from app.schemas.image import TaskStatus

logger = logging.getLogger(__name__)

STATUS_PENDING: TaskStatus = "PENDING"
STATUS_COMPLETED: TaskStatus = "COMPLETED"
STATUS_FAILED: TaskStatus = "FAILED"

MOCK_IMAGE_URL = "http://dummy-s3/image.png"


async def create_image_task(session: AsyncSession, task_id: UUID, prompt: str) -> None:
    """Insert a new task row into the database."""

    session.add(
        ImageTask(
            id=str(task_id),
            prompt=prompt,
            status=STATUS_PENDING,
            image_url=None,
        )
    )
    await session.commit()


async def get_task_status(session: AsyncSession, task_id: UUID) -> Optional[TaskStatus]:
    """Fetch the current status for a task."""

    result = await session.execute(
        select(ImageTask.status).where(ImageTask.id == str(task_id))
    )
    return result.scalar_one_or_none()


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


async def generate_image_task(ctx: dict[str, Any], task_id: str) -> None:
    """Call SD WebUI txt2img, then update task row."""

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

    try:
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                settings.sd_api_url,
                json={"prompt": prompt, "steps": 20},
            )
    except (httpx.TimeoutException, httpx.RequestError):
        logger.exception("SD API request failed for task_id=%s", task_id)
        await _update_task(task_uuid, status=STATUS_FAILED)
        return

    if response.is_success:
        await _update_task(
            task_uuid,
            status=STATUS_COMPLETED,
            image_url=MOCK_IMAGE_URL,
        )
        return

    logger.error(
        "SD API returned error status=%s task_id=%s body=%s",
        response.status_code,
        task_id,
        response.text[:500],
    )
    await _update_task(task_uuid, status=STATUS_FAILED)
