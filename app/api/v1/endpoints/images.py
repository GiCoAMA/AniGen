from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.image import ApiResponse, ImageGenerateRequest
from app.db.database import get_db
from app.services.image_service import (
    STATUS_PENDING,
    create_image_task,
    get_task_status,
)

router = APIRouter()


@router.post("/generate", status_code=200)
async def generate_image(
    req: Request,
    payload: ImageGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    task_id = uuid4()

    await create_image_task(db, task_id=task_id, prompt=payload.prompt)

    redis = req.app.state.redis
    await redis.enqueue_job("generate_image_task", str(task_id))

    data = {"task_id": task_id, "status": STATUS_PENDING}
    return ApiResponse(code=0, data=data, msg="success")


@router.get("/tasks/{task_id}", status_code=200)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    status = await get_task_status(db, task_id)
    if status is None:
        payload = ApiResponse(code=1, data={}, msg="task not found")
        return JSONResponse(status_code=404, content=payload.model_dump(mode="json"))

    data = {"task_id": task_id, "status": status}
    payload = ApiResponse(code=0, data=data, msg="success")
    return JSONResponse(status_code=200, content=payload.model_dump(mode="json"))

