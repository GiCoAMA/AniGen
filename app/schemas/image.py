from datetime import datetime
from typing import Generic, Literal, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

TaskStatus = Literal["PENDING", "COMPLETED", "FAILED"]

API_CODE_SUCCESS: int = 0
API_MSG_SUCCESS: str = "success"

TData = TypeVar("TData")


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Text prompt for image generation.",
    )
    width: int = Field(default=512, ge=256, le=1024)
    height: int = Field(default=512, ge=256, le=1024)
    steps: int = Field(default=20, ge=1, le=50)


class ImageGenerateResponseData(BaseModel):
    task_id: UUID
    status: TaskStatus
    user_id: int = Field(description="Owner user id for this task.")
    image_url: Optional[str] = Field(
        default=None,
        description="Relative URL to the generated image under /static/images when completed.",
    )


class ImageTaskListItem(BaseModel):
    id: UUID = Field(description="Task identifier (UUID).")
    prompt: str = Field(description="Original prompt for this task.")
    status: TaskStatus = Field(description="Current status of the task.")
    image_url: Optional[str] = Field(
        default=None,
        description="Relative URL to the generated image under /static/images when completed.",
    )
    created_at: datetime = Field(description="Creation time of the task.")


class ImageTaskListResponseData(BaseModel):
    items: list[ImageTaskListItem] = Field(
        default_factory=list,
        description="Tasks for the current user ordered by creation time (desc).",
    )


class ApiResponse(BaseModel, Generic[TData]):
    """Unified API envelope; use `ApiResponse[ImageGenerateResponseData]` in routes for OpenAPI."""

    code: int
    data: TData
    msg: str
