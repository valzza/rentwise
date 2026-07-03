import json
from typing import Optional, Any

from app.repositories.audit_repository import AuditRepository


def _serialize(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


class AuditService:
    """Writes immutable audit-trail rows. Never commits — the caller's
    request handler owns the transaction boundary."""

    def __init__(self, repo: AuditRepository):
        self.repo = repo

    async def log(
        self,
        *,
        action: str,
        entity: str,
        user_id: Optional[int] = None,
        entity_id: Optional[int] = None,
        old_value: Any = None,
        new_value: Any = None,
        ip_address: Optional[str] = None,
    ) -> None:
        try:
            await self.repo.create(
                user_id=user_id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                old_value=_serialize(old_value),
                new_value=_serialize(new_value),
                ip_address=ip_address,
                created_by=user_id,
                updated_by=user_id,
            )
        except Exception:
            # Auditing must never break the primary operation.
            pass