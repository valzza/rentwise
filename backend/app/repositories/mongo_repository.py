import logging
from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.database import mongo_db

logger = logging.getLogger("rentwise.mongo")


def _serialize_chat_doc(doc: dict) -> dict:
    """JSON-safe dict for Socket.IO emits (datetime/ObjectId are not serializable)."""
    out = dict(doc)
    if out.get("_id") is not None:
        out["_id"] = str(out["_id"])
    ts = out.get("timestamp")
    if isinstance(ts, datetime):
        out["timestamp"] = ts.isoformat()
    return out


class MongoRepository:
    """
    Wrapper around the 4 MongoDB collections. Every operation degrades
    gracefully: if MongoDB is unreachable, writes are skipped (logged as a
    warning) and reads return empty results, so core PostgreSQL-backed
    features keep working even when MongoDB is down.
    """

    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db or mongo_db

    # ── ML prediction history ─────────────────────────────────────────────
    async def log_prediction(
        self,
        property_id: Optional[int],
        features: dict,
        prediction: dict,
        model_version: str,
    ) -> None:
        try:
            await self.db["ml_prediction_history"].insert_one({
                "property_id": property_id,
                "features": features,
                "prediction": prediction,
                "model_version": model_version,
                "timestamp": datetime.now(timezone.utc),
            })
        except Exception as e:
            logger.warning(f"MongoDB log_prediction skipped: {e}")

    # ── Property search logs ──────────────────────────────────────────────
    async def log_search(self, user_id: Optional[int], query_params: dict, results_count: int) -> None:
        try:
            await self.db["property_search_logs"].insert_one({
                "user_id": user_id,
                "query_params": query_params,
                "results_count": results_count,
                "timestamp": datetime.now(timezone.utc),
            })
        except Exception as e:
            logger.warning(f"MongoDB log_search skipped: {e}")

    # ── Chat messages ─────────────────────────────────────────────────────
    async def save_message(self, room_id: str, sender_id: int, message: str) -> dict:
        doc = {
            "room_id": room_id,
            "sender_id": sender_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc),
            "is_read": False,
        }
        try:
            result = await self.db["chat_messages"].insert_one(doc)
            doc["_id"] = str(result.inserted_id)
        except Exception as e:
            logger.warning(f"MongoDB save_message skipped: {e}")
            doc["_id"] = None
        return _serialize_chat_doc(doc)

    async def get_messages(self, room_id: str, limit: int = 50) -> list:
        try:
            cursor = self.db["chat_messages"].find(
                {"room_id": room_id}
            ).sort("timestamp", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
            return list(reversed([_serialize_chat_doc(d) for d in docs]))
        except Exception as e:
            logger.warning(f"MongoDB get_messages failed, returning empty: {e}")
            return []

    async def mark_messages_read(self, room_id: str, reader_id: int) -> None:
        try:
            await self.db["chat_messages"].update_many(
                {"room_id": room_id, "sender_id": {"$ne": reader_id}},
                {"$set": {"is_read": True}},
            )
        except Exception as e:
            logger.warning(f"MongoDB mark_messages_read skipped: {e}")

    # ── Notification events ───────────────────────────────────────────────
    async def log_notification_event(self, user_id: int, type: str, payload: dict) -> None:
        try:
            await self.db["notification_events"].insert_one({
                "user_id": user_id,
                "type": type,
                "payload": payload,
                "delivered_at": datetime.now(timezone.utc),
            })
        except Exception as e:
            logger.warning(f"MongoDB log_notification_event skipped: {e}")
