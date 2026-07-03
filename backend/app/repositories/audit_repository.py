from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.audit_models import AuditLog


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> AuditLog:
        log = AuditLog(**kwargs)
        self.db.add(log)
        await self.db.flush()
        return log

    async def list(self, entity: Optional[str], page: int, page_size: int) -> Tuple[List[AuditLog], int]:
        filters = []
        if entity:
            filters.append(AuditLog.entity == entity)
        where_clause = and_(*filters) if filters else True
        total = (await self.db.execute(select(func.count()).select_from(AuditLog).where(where_clause))).scalar_one()
        result = await self.db.execute(
            select(AuditLog).where(where_clause)
            .order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total