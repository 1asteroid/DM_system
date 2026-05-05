from fastapi import APIRouter, Query, status
from fastapi.websockets import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import SessionLocal
from ..core.security import decode_token
from ..models.models import User

router = APIRouter(tags=["websocket"])

# user_id -> websocket connection
active_connections: dict[int, WebSocket] = {}


async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """Extract user from JWT token."""
    try:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None

        sub = payload.get("sub")
        if not sub:
            return None

        result = await db.execute(select(User).where(User.id == int(sub)))
        user = result.scalar_one_or_none()
        return user if user and user.is_active else None
    except Exception:
        return None


async def _broadcast(payload: dict, except_user_id: int | None = None):
    stale_user_ids: list[int] = []
    for uid, ws in list(active_connections.items()):
        if except_user_id is not None and uid == except_user_id:
            continue
        try:
            await ws.send_json(payload)
        except Exception:
            stale_user_ids.append(uid)

    for uid in stale_user_ids:
        active_connections.pop(uid, None)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = Query(None)):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()

    # Backward compatibility: allow auth token to be sent as first WS message.
    if not token:
        try:
            auth_msg = await websocket.receive_json()
            if isinstance(auth_msg, dict):
                token = auth_msg.get("token")
        except Exception:
            token = None

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
        return

    async with SessionLocal() as db:
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

        # Keep only latest connection for this user.
        old_ws = active_connections.get(user.id)
        if old_ws and old_ws is not websocket:
            try:
                await old_ws.close()
            except Exception:
                pass

        active_connections[user.id] = websocket

        await websocket.send_json({"type": "online_users", "user_ids": list(active_connections.keys())})
        await _broadcast({"type": "user_online", "user_id": user.id}, except_user_id=user.id)

        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            current_ws = active_connections.get(user.id)
            if current_ws is websocket:
                active_connections.pop(user.id, None)
                await _broadcast({"type": "user_offline", "user_id": user.id}, except_user_id=user.id)


async def send_to_user(user_id: int, message: dict):
    """Send message to specific user if connected."""
    ws = active_connections.get(user_id)
    if not ws:
        return

    try:
        await ws.send_json(message)
    except Exception:
        active_connections.pop(user_id, None)
