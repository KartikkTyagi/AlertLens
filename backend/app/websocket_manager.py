import os
import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger("uvicorn.error")

MAX_WS_CONNECTIONS = int(os.getenv("MAX_WS_CONNECTIONS", "100"))


class ConnectionManager:
    """Manages active WebSocket connections and thread-safe broadcasts with resource safeguards."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> bool:
        if len(self.active_connections) >= MAX_WS_CONNECTIONS:
            logger.warning(
                "WebSocket connection rejected: max limit of %d reached", MAX_WS_CONNECTIONS
            )
            await websocket.close(code=1013, reason="Service overloaded")
            return False

        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket client connected. Active connections: %d",
            len(self.active_connections),
        )
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                "WebSocket client disconnected. Active connections: %d",
                len(self.active_connections),
            )

    async def broadcast(self, message: dict):
        """Broadcast a JSON message to all connected clients.
        
        Silently prunes stale or disconnected clients so a broken socket
        never crashes the broadcast loop for other clients.
        """
        if not self.active_connections:
            return

        disconnected: List[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("Error broadcasting to WebSocket client: %s", e)
                disconnected.append(connection)

        # Remove failed connections
        for conn in disconnected:
            self.disconnect(conn)

    @property
    def count(self) -> int:
        return len(self.active_connections)

    def clear(self):
        """Clears all active connections (used for testing and teardown)."""
        self.active_connections.clear()


# Global singleton instance
manager = ConnectionManager()
