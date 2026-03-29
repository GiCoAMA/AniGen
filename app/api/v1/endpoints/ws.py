"""WebSocket endpoints (task status push)."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status as starlette_status
from starlette.websockets import WebSocketDisconnect

from app.api.deps import get_current_user_ws, get_db
from app.models.user import User
from app.services.image_service import get_task_status_image_url_for_access_check

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/tasks/{task_id}")
async def task_status_ws(
    websocket: WebSocket,
    task_id: UUID,
    current_user: User = Depends(get_current_user_ws),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Poll task row server-side and push JSON updates until terminal state."""

    await websocket.accept()
    try:
        while True:
            row = await get_task_status_image_url_for_access_check(session, task_id)
            if row is None:
                await websocket.close(
                    code=starlette_status.WS_1008_POLICY_VIOLATION,
                    reason="Task not found",
                )
                return
            task_status, image_url, owner_id = row
            if owner_id != current_user.id:
                await websocket.close(
                    code=starlette_status.WS_1008_POLICY_VIOLATION,
                    reason="Forbidden",
                )
                return

            payload = {"status": task_status, "image_url": image_url}
            await websocket.send_json(payload)

            if task_status in ("COMPLETED", "FAILED"):
                await websocket.close()
                return

            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected task_id=%s", task_id)
    except Exception:
        logger.exception("WebSocket task stream error task_id=%s", task_id)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except Exception:
            pass
