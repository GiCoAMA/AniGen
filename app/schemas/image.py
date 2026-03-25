from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

TaskStatus = Literal["PENDING", "COMPLETED", "FAILED"]


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Text prompt for image generation.")


class ImageGenerateResponseData(BaseModel):
    task_id: UUID
    status: TaskStatus


class ApiResponse(BaseModel):
    code: int
    data: dict[str, Any] = Field(default_factory=dict)
    msg: str

