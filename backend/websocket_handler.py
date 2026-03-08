"""
Claw Office UI - WebSocket Handler

Real-time event broadcasting using Flask-SocketIO.
"""

from flask_socketio import SocketIO, emit

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


def init_websocket(app):
    """Initialize WebSocket with Flask app."""
    socketio.init_app(app)
    return socketio


def broadcast_agent_update(agent_data: dict):
    """Broadcast agent state change to all connected clients."""
    socketio.emit("agent.state_changed", agent_data, namespace="/")


def broadcast_agent_joined(agent_data: dict):
    """Broadcast new agent joined."""
    socketio.emit("agent.joined", agent_data, namespace="/")


def broadcast_agent_left(agent_id: str):
    """Broadcast agent left."""
    socketio.emit("agent.left", {"agentId": agent_id}, namespace="/")


def broadcast_task_event(event_type: str, task_data: dict):
    """Broadcast task events (created, assigned, completed, etc.)."""
    socketio.emit(f"task.{event_type}", task_data, namespace="/")


def broadcast_message(message_data: dict):
    """Broadcast inter-agent message."""
    socketio.emit("message.new", message_data, namespace="/")


@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    emit("connected", {"status": "ok"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    pass


@socketio.on("ping")
def handle_ping():
    """Handle ping for keepalive."""
    emit("pong", {"status": "ok"})
