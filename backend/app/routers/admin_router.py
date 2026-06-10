from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, or_, and_, delete
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db, require_role
from app.models.user_models import User, UserRole, Role
from app.models.domain_models import Property, LeaseContract, Payment
from app.models.audit_models import AuditLog, Setting
from app.schemas.user_schemas import UserOut, UserUpdateRequest

router = APIRouter()


def _user_to_out(user: User) -> dict:
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "roles": [ur.role.name for ur in user.user_roles] if user.user_roles else [],
    }


def _property_to_out(p: Property) -> dict:
    # Explicit field list — never return the tsvector column (not JSON serializable)
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


@router.get("/users")
async def list_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if search:
        filters.append(
            or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )
    if is_active is not None:
        filters.append(User.is_active == is_active)
    if role:
        filters.append(
            User.id.in_(
                select(UserRole.user_id).join(Role, Role.id == UserRole.role_id).where(Role.name == role)
            )
        )

    where_clause = and_(*filters) if filters else True

    total = (await db.execute(select(func.count()).select_from(User).where(where_clause))).scalar_one()
    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(where_clause)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    users = result.scalars().all()

    return {
        "items": [_user_to_out(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdateRequest,
    _: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    updates = data.model_dump(exclude_none=True)
    if updates:
        await db.execute(update(User).where(User.id == user_id).values(**updates))
        await db.commit()

    result = await db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.id == user_id)
    )
    return _user_to_out(result.scalar_one())


@router.get("/reports")
async def platform_reports(
    _: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    total_properties = (await db.execute(select(func.count()).select_from(Property).where(Property.status != "deleted"))).scalar_one()
    active_leases = (await db.execute(select(func.count()).select_from(LeaseContract).where(LeaseContract.status == "active"))).scalar_one()
    monthly_revenue = (
        await db.execute(
            select(func.sum(Payment.amount)).where(Payment.status == "completed")
        )
    ).scalar_one() or 0

    return {
        "total_users": total_users,
        "total_properties": total_properties,
        "active_leases": active_leases,
        "total_revenue": float(monthly_revenue),
    }


@router.get("/properties")
async def all_properties(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if status:
        filters.append(Property.status == status)
    where_clause = and_(*filters) if filters else True
    total = (await db.execute(select(func.count()).select_from(Property).where(where_clause))).scalar_one()
    result = await db.execute(
        select(Property).where(where_clause)
        .order_by(Property.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    return {
        "items": [_property_to_out(p) for p in result.scalars().all()],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/audit-logs")
async def audit_logs(
    entity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if entity:
        filters.append(AuditLog.entity == entity)
    where_clause = and_(*filters) if filters else True
    total = (await db.execute(select(func.count()).select_from(AuditLog).where(where_clause))).scalar_one()
    result = await db.execute(
        select(AuditLog).where(where_clause)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    logs = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "entity": log.entity,
            "entity_id": log.entity_id,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
        }
        for log in result.scalars().all()
    ]
    return {"items": logs, "total": total, "page": page, "page_size": page_size}


@router.get("/settings")
async def list_settings(
    _: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Setting))
    return [
        {"id": s.id, "key": s.key, "value": s.value, "description": s.description}
        for s in result.scalars().all()
    ]


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    value: str,
    _: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(update(Setting).where(Setting.key == key).values(value=value))
    await db.commit()
    return {"key": key, "value": value}
