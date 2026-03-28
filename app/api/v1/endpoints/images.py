from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.image import (
    API_CODE_SUCCESS,
    API_MSG_SUCCESS,
    ApiResponse,
    ImageGenerateRequest,
    ImageGenerateResponseData,
)
from app.db.database import get_db
from app.services.image_service import (
    STATUS_PENDING,
    create_image_task,
    get_task_status_and_image_url,
)

router = APIRouter()


@router.post(
    "/generate",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ImageGenerateResponseData],
)
async def generate_image(
    req: Request,
    payload: ImageGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ImageGenerateResponseData]:
    task_id = uuid4()

    await create_image_task(db, task_id=task_id, prompt=payload.prompt)

    redis = req.app.state.redis
    await redis.enqueue_job("generate_image_task", str(task_id))

    return ApiResponse(
        code=API_CODE_SUCCESS,
        data=ImageGenerateResponseData(
            task_id=task_id,
            status=STATUS_PENDING,
            image_url=None,
        ),
        msg=API_MSG_SUCCESS,
    )


@router.get(
    "/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ImageGenerateResponseData],
)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ImageGenerateResponseData]:
    row = await get_task_status_and_image_url(db, task_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    task_status, image_url = row

    return ApiResponse(
        code=API_CODE_SUCCESS,
        data=ImageGenerateResponseData(
            task_id=task_id,
            status=task_status,
            image_url=image_url,
        ),
        msg=API_MSG_SUCCESS,
    )
