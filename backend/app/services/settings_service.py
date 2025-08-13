from sqlalchemy.orm import Session
from ..models.app_setting import AppSetting
from ..core.config import settings


class SettingsService:
    def get(self, db: Session) -> AppSetting:
        row = db.query(AppSetting).first()
        if not row:
            row = AppSetting(
                id="global",
                project_name=settings.PROJECT_NAME,
                allow_registration=settings.ALLOW_REGISTRATION,
            )
            db.add(row);
            db.commit();
            db.refresh(row)
        return row

    def update(self, db: Session, *, project_name=None, allow_registration=None) -> AppSetting:
        row = self.get(db)
        if project_name is not None:
            row.project_name = project_name
        if allow_registration is not None:
            row.allow_registration = allow_registration
        db.commit();
        db.refresh(row)
        return row


settings_service = SettingsService()
