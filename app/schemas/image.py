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


class ImageGenerateResponseData(BaseModel):
    task_id: UUID
    status: TaskStatus
    image_url: Optional[str] = Field(
        default=None,
        description="Relative URL to the generated image under /static/images when completed.",
    )


class ApiResponse(BaseModel, Generic[TData]):
    """Unified API envelope; use `ApiResponse[ImageGenerateResponseData]` in routes for OpenAPI."""

    code: int
    data: TData
    msg: str
