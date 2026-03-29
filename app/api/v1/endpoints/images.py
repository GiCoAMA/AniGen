from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimiter, get_current_user
from app.schemas.image import (
    API_CODE_SUCCESS,
    API_MSG_SUCCESS,
    ApiResponse,
    ImageGenerateRequest,
    ImageGenerateResponseData,
)
from app.db.database import get_db
from app.models.user import User
from app.services.image_service import (
    STATUS_PENDING,
    create_image_task,
    get_task_status_image_url_for_access_check,
)

router = APIRouter()

_generate_rate_limit = RateLimiter(times=5, seconds=60, key_suffix="generate")


@router.post(
    "/generate",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ImageGenerateResponseData],
)
async def generate_image(
    req: Request,
    payload: ImageGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(_generate_rate_limit),
) -> ApiResponse[ImageGenerateResponseData]:
    task_id = uuid4()

    await create_image_task(
        db,
        task_id=task_id,
        prompt=payload.prompt,
        user_id=current_user.id,
        width=payload.width,
        height=payload.height,
        steps=payload.steps,
    )

    redis = req.app.state.redis
    await redis.enqueue_job(
        "generate_image_task",
        str(task_id),
        payload.width,
        payload.height,
        payload.steps,
    )

    return ApiResponse(
        code=API_CODE_SUCCESS,
        data=ImageGenerateResponseData(
            task_id=task_id,
            status=STATUS_PENDING,
            user_id=current_user.id,
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
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ImageGenerateResponseData]:
    row = await get_task_status_image_url_for_access_check(db, task_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    task_status, image_url, owner_id = row
    if owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this task",
        )

    assert owner_id is not None

    return ApiResponse(
        code=API_CODE_SUCCESS,
        data=ImageGenerateResponseData(
            task_id=task_id,
            status=task_status,
            user_id=owner_id,
            image_url=image_url,
        ),
        msg=API_MSG_SUCCESS,
    )
