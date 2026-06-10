from app.websockets.socket_manager import sio
from app.core.security import decode_access_token
from jose import JWTError


@sio.on("connect")
async def on_connect(sid: str, environ: dict, auth: dict = None):
    """
    Authenticate the Socket.IO connection via JWT token in the auth payload.
    Clients must pass: { token: "<access_token>" }
    On success the user joins their personal notification room.
    """
    token = (auth or {}).get("token")
    if not token:
        # Reject unauthenticated connections
        return False

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return False

    await sio.save_session(sid, {"user_id": user_id})
    await sio.enter_room(sid, f"user:{user_id}")


@sio.on("disconnect")
async def on_disconnect(sid: str):
    pass  # Rooms are cleaned up automatically by python-socketio on disconnect
