import socketio
from fastapi import FastAPI
from app.core.config import settings

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.ALLOWED_ORIGINS,
    logger=False,
    engineio_logger=False,
)


def create_socket_app(fastapi_app: FastAPI) -> socketio.ASGIApp:
    """Wrap the FastAPI ASGI app with Socket.IO. Called from main.py after the FastAPI app is built."""
    # Import handlers here so event decorators register against sio before the app starts
    from app.websockets import chat_handlers  # noqa: F401
    from app.websockets import notification_handlers  # noqa: F401
    return socketio.ASGIApp(sio, other_asgi_app=fastapi_app)


async def emit_notification(user_id: int, payload: dict) -> None:
    """Emit a live notification into a user's personal Socket.IO room."""
    await sio.emit("notification", payload, room=f"user:{user_id}")
