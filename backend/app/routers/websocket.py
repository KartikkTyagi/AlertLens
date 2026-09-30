import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..websocket_manager import manager

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/incidents")
async def websocket_incidents_endpoint(websocket: WebSocket):
    """Real-time server-to-client push channel for new incidents."""
    connected = await manager.connect(websocket)
    if not connected:
        return
    try:
        # Keep connection alive while listening for client disconnects / pings
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket exception for client: %s", e)
        manager.disconnect(websocket)
