from fastapi import APIRouter, Depends, Query, UploadFile, File as FastFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role, require_permission, get_audit_service
from app.services.audit_service import AuditService
from app.services.export_service import ExportService
from app.models.user_models import User

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> ExportService:
    return ExportService(db)


@router.get("/export/{entity}")
async def export_entity(
    entity: str,
    format: str = Query("csv", pattern="^(csv|xlsx|excel|json)$"),
    current_user: User = Depends(require_permission("data:export")),
    svc: ExportService = Depends(_svc),
    audit: AuditService = Depends(get_audit_service),
    db: AsyncSession = Depends(get_db),
):
    content, media_type, filename = await svc.export(entity, format)
    await audit.log(action="export", entity=entity, user_id=current_user.id,
                    new_value={"format": format})
    await db.commit()
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import/{entity}")
async def import_entity(
    entity: str,
    file: UploadFile = FastFile(...),
    current_user: User = Depends(require_role("admin")),
    svc: ExportService = Depends(_svc),
    audit: AuditService = Depends(get_audit_service),
    db: AsyncSession = Depends(get_db),
):
    raw = await file.read()
    result = await svc.import_rows(entity, raw, file.content_type or "")
    await audit.log(action="import", entity=entity, user_id=current_user.id, new_value=result)
    await db.commit()
    return result
