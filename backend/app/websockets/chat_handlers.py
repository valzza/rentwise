from app.websockets.socket_manager import sio
from app.repositories.mongo_repository import MongoRepository


def _room_id(property_id: int, user_a: int, user_b: int) -> str:
    """Deterministic room name for a (property, pair) combination."""
    lo, hi = sorted([user_a, user_b])
    return f"chat:{property_id}:{lo}_{hi}"


@sio.on("join_chat")
async def join_chat(sid: str, data: dict):
    """
    Expected payload: { property_id, other_user_id }
    The current user's id is stored in sio's session after authentication.
    """
    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return

    property_id = data.get("property_id")
    other_user_id = data.get("other_user_id")
    room = _room_id(property_id, user_id, other_user_id)

    await sio.enter_room(sid, room)

    # Send the last 50 messages to the joining user
    mongo = MongoRepository()
    messages = await mongo.get_messages(room)
    await mongo.mark_messages_read(room, user_id)
    await sio.emit("chat_history", messages, to=sid)


@sio.on("send_message")
async def send_message(sid: str, data: dict):
    """
    Expected payload: { property_id, other_user_id, message }
    """
    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return

    property_id = data.get("property_id")
    other_user_id = data.get("other_user_id")
    message_text = data.get("message", "").strip()
    if not message_text:
        return

    room = _room_id(property_id, user_id, other_user_id)
    mongo = MongoRepository()
    saved = await mongo.save_message(room, user_id, message_text)

    await sio.emit("new_message", saved, room=room)


@sio.on("mark_read")
async def mark_read(sid: str, data: dict):
    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    if not user_id:
        return

    property_id = data.get("property_id")
    other_user_id = data.get("other_user_id")
    room = _room_id(property_id, user_id, other_user_id)

    mongo = MongoRepository()
    await mongo.mark_messages_read(room, user_id)
