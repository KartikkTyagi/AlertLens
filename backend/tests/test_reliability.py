import asyncio
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.websocket_manager import ConnectionManager, manager
import app.websocket_manager as wm

client = TestClient(app)


def test_ws_connection_and_heartbeat():
    """Verify WebSocket accepts connection and responds to keepalive ping with pong."""
    with client.websocket_connect("/ws/incidents") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert data == "pong"


def test_ws_disconnect_cleanup():
    """Verify active connection count increments on connect and decrements on disconnect."""
    initial_count = manager.count
    with client.websocket_connect("/ws/incidents"):
        assert manager.count == initial_count + 1
    # After exiting context, client disconnects
    assert manager.count == initial_count


def test_ws_broadcast_to_multiple_clients():
    """Verify broadcast delivers payload to all connected clients."""
    with client.websocket_connect("/ws/incidents") as ws1:
        with client.websocket_connect("/ws/incidents") as ws2:
            test_payload = {
                "type": "NEW_INCIDENT",
                "incident": {
                    "id": "inc-test-reliability",
                    "severity_score": 19.5,
                    "mitre_technique": "T1078",
                },
            }
            # Broadcast asynchronously
            asyncio.run(manager.broadcast(test_payload))

            data1 = ws1.receive_json()
            data2 = ws2.receive_json()

            assert data1 == test_payload
            assert data2 == test_payload


def test_ws_unexpected_text_does_not_crash():
    """Verify client sending non-ping text does not crash the server loop."""
    with client.websocket_connect("/ws/incidents") as ws:
        ws.send_text("hello-world")
        # Ensure connection is still responsive to ping
        ws.send_text("ping")
        resp = ws.receive_text()
        assert resp == "pong"


def test_ws_stale_connection_pruning():
    """Verify that broken or stale connections are automatically pruned during broadcast."""
    local_manager = ConnectionManager()

    # Create one healthy mock socket and one failing mock socket
    healthy_ws = AsyncMock()
    broken_ws = AsyncMock()
    broken_ws.send_json.side_effect = RuntimeError("Connection reset by peer")

    local_manager.active_connections.append(healthy_ws)
    local_manager.active_connections.append(broken_ws)
    assert local_manager.count == 2

    # Broadcast message
    asyncio.run(local_manager.broadcast({"type": "PING"}))

    # Healthy received message
    healthy_ws.send_json.assert_awaited_once_with({"type": "PING"})
    # Broken was pruned
    assert broken_ws not in local_manager.active_connections
    assert local_manager.count == 1
    assert healthy_ws in local_manager.active_connections


def test_ws_connection_limit_rejection(monkeypatch):
    """Verify WebSocket connection is rejected with 1013 when connection limit is reached."""
    monkeypatch.setattr(wm, "MAX_WS_CONNECTIONS", 1)
    local_manager = ConnectionManager()

    # Connect first client
    mock_ws1 = AsyncMock()
    success1 = asyncio.run(local_manager.connect(mock_ws1))
    assert success1 is True
    assert local_manager.count == 1

    # Attempt to connect second client exceeding cap
    mock_ws2 = AsyncMock()
    success2 = asyncio.run(local_manager.connect(mock_ws2))
    assert success2 is False
    assert local_manager.count == 1
    mock_ws2.close.assert_awaited_once_with(code=1013, reason="Service overloaded")
