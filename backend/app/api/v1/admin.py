from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...api.deps import get_db, get_current_superuser
from ...schemas.settings import SettingsResponse, SettingsUpdate
from ...services.settings_service import settings_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(db: Session = Depends(get_db), _: str = Depends(get_current_superuser)):
    return settings_service.get(db)


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
        payload: SettingsUpdate,
        db: Session = Depends(get_db),
        _: str = Depends(get_current_superuser),
):
    return settings_service.update(db, **payload.dict(exclude_unset=True))
