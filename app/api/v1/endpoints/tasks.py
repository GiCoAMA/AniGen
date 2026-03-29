from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud_task import get_tasks_by_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.image import (
    API_CODE_SUCCESS,
    API_MSG_SUCCESS,
    ApiResponse,
    ImageTaskListItem,
    ImageTaskListResponseData,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ImageTaskListResponseData],
)
async def list_tasks(
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[ImageTaskListResponseData]:
    tasks = await get_tasks_by_user(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )

    items: list[ImageTaskListItem] = []
    for task in tasks:
        items.append(
            ImageTaskListItem(
                id=UUID(task.id),
                prompt=task.prompt,
                status=task.status,
                image_url=task.image_url,
                created_at=task.created_at,
            )
        )

    data = ImageTaskListResponseData(items=items)
    return ApiResponse(code=API_CODE_SUCCESS, data=data, msg=API_MSG_SUCCESS)

