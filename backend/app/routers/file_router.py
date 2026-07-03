from fastapi import APIRouter, Depends, File as FastFile, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user_models import User
from app.repositories.file_repository import FileRepository
from app.services.file_service import FileService
from app.schemas.file_schemas import FileOut

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_db)) -> FileService:
    return FileService(FileRepository(db))


@router.post("/upload", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastFile(...),
    entity: str = Form("misc"),
    entity_id: int = Form(0),
    link_property: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: FileService = Depends(_svc),
):
    """Upload a single file (image). For property photos send
    entity="property", entity_id=<property id>, link_property=true."""
    record = await svc.upload(
        upload=file,
        entity=entity,
        entity_id=entity_id,
        uploaded_by=current_user.id,
        link_property=link_property,
    )
    await db.commit()
    await db.refresh(record)
    return record
