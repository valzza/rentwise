from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, or_, and_
from sqlalchemy.orm import selectinload

from app.models.user_models import User, UserRole, Role
from app.models.domain_models import Property, LeaseContract, Payment
from app.models.audit_models import Setting
from app.repositories.audit_repository import AuditRepository


def user_to_out(user: User) -> dict:
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "roles": [ur.role.name for ur in user.user_roles] if user.user_roles else [],
    }


def property_to_out(p: Property) -> dict:
    return {
        "id": p.id,
        "landlord_id": p.landlord_id,
        "title": p.title,
        "price": float(p.price),
        "city_id": p.city_id,
        "size_m2": float(p.size_m2),
        "num_rooms": p.num_rooms,
        "status": p.status,
        "created_at": p.created_at,
    }


class AdminService:
    """All admin read/aggregate logic, kept out of the router."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self, search, role, is_active, page, page_size) -> dict:
        filters = []
        if search:
            filters.append(or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            ))
        if is_active is not None:
            filters.append(User.is_active == is_active)
        if role:
            filters.append(User.id.in_(
                select(UserRole.user_id).join(Role, Role.id == UserRole.role_id).where(Role.name == role)
            ))
        where_clause = and_(*filters) if filters else True
        total = (await self.db.execute(select(func.count()).select_from(User).where(where_clause))).scalar_one()
        result = await self.db.execute(
            select(User).options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(where_clause).order_by(User.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        return {"items": [user_to_out(u) for u in result.scalars().all()],
                "total": total, "page": page, "page_size": page_size}

    async def update_user(self, user_id: int, updates: dict) -> dict:
        if updates:
            await self.db.execute(update(User).where(User.id == user_id).values(**updates))
            await self.db.flush()
        result = await self.db.execute(
            select(User).options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        return user_to_out(result.scalar_one())

    async def reports(self, date_from: Optional[datetime], date_to: Optional[datetime]) -> dict:
        pay_filters = [Payment.status == "completed"]
        if date_from:
            pay_filters.append(Payment.created_at >= date_from)
        if date_to:
            pay_filters.append(Payment.created_at <= date_to)

        total_users = (await self.db.execute(select(func.count()).select_from(User))).scalar_one()
        total_properties = (await self.db.execute(
            select(func.count()).select_from(Property).where(Property.status != "deleted")
        )).scalar_one()
        active_leases = (await self.db.execute(
            select(func.count()).select_from(LeaseContract).where(LeaseContract.status == "active")
        )).scalar_one()
        total_revenue = (await self.db.execute(
            select(func.sum(Payment.amount)).where(and_(*pay_filters))
        )).scalar_one() or 0

        # Monthly revenue breakdown (for charts)
        monthly_rows = (await self.db.execute(
            select(
                func.to_char(Payment.created_at, "YYYY-MM").label("month"),
                func.sum(Payment.amount).label("total"),
            ).where(and_(*pay_filters)).group_by("month").order_by("month")
        )).all()

        return {
            "total_users": total_users,
            "total_properties": total_properties,
            "active_leases": active_leases,
            "total_revenue": float(total_revenue),
            "monthly": [{"month": r.month, "total": float(r.total)} for r in monthly_rows],
        }

    async def all_properties(self, status_filter, page, page_size) -> dict:
        filters = []
        if status_filter:
            filters.append(Property.status == status_filter)
        where_clause = and_(*filters) if filters else True
        total = (await self.db.execute(select(func.count()).select_from(Property).where(where_clause))).scalar_one()
        result = await self.db.execute(
            select(Property).where(where_clause).order_by(Property.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        return {"items": [property_to_out(p) for p in result.scalars().all()],
                "total": total, "page": page, "page_size": page_size}

    async def audit_logs(self, entity, page, page_size) -> dict:
        logs, total = await AuditRepository(self.db).list(entity, page, page_size)
        return {
            "items": [{
                "id": log.id, "user_id": log.user_id, "action": log.action,
                "entity": log.entity, "entity_id": log.entity_id,
                "ip_address": log.ip_address, "created_at": log.created_at,
            } for log in logs],
            "total": total, "page": page, "page_size": page_size,
        }

    async def list_settings(self) -> list:
        result = await self.db.execute(select(Setting))
        return [{"id": s.id, "key": s.key, "value": s.value, "description": s.description}
                for s in result.scalars().all()]

    async def update_setting(self, key: str, value: str) -> dict:
        await self.db.execute(update(Setting).where(Setting.key == key).values(value=value))
        await self.db.flush()
        return {"key": key, "value": value}