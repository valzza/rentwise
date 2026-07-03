from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db
from app.models.audit_models import Setting

router = APIRouter()

# Keys exposed publicly to drive the static landing-page content (CMS).
PUBLIC_KEYS = ("homepage_title", "homepage_slogan", "welcome_message")


@router.get("/public", response_model=Dict[str, str])
async def public_settings(db: AsyncSession = Depends(get_db)):
    """Static homepage content editable by admins via the CMS — no auth needed."""
    result = await db.execute(select(Setting).where(Setting.key.in_(PUBLIC_KEYS)))
    return {s.key: s.value for s in result.scalars().all()}
