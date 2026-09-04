from datetime import datetime, timedelta, timezone
from typing import Any, cast
from uuid import UUID

from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.upload import Upload
from app.schemas.upload import UploadCreate, UploadUpdate


class CRUDUpload(CRUDBase[Upload, UploadCreate, UploadUpdate]):
    def create_with_user(
        self, db: Session, upload_id: str, user_id: UUID, is_uploading: bool = True
    ) -> Upload:
        """Create new upload event.

        Args:
            db (Session): Database session.
            upload_id (str): Upload event ID from tusd.
            user_id (UUID): ID of user uploading file.
            is_uploading (bool, optional): Current status of upload. Defaults to True.

        Returns:
            Upload: Newly created upload instance.
        """
        upload_in = UploadCreate(
            upload_id=upload_id, user_id=user_id, is_uploading=is_uploading
        )
        upload = self.model(**upload_in.model_dump())
        with db as session:
            session.add(upload)
            session.commit()
            session.refresh(upload)

        return upload

    def get_upload_by_upload_id(self, db: Session, upload_id: str) -> Upload | None:
        """Find upload record by unique upload ID.

        Args:
            db (Session): Database session
            upload_id (str): Upload event ID from tusd.

        Returns:
            Upload | None: Upload record or None if record matching ID not found.
        """
        statement = select(Upload).where(Upload.upload_id == upload_id)
        with db as session:
            upload = session.scalar(statement)
            return upload

    def count_stale(self, db: Session, older_than: timedelta) -> int:
        """Count upload records that have aged past the retention window.

        Args:
            db (Session): Database session.
            older_than (timedelta): Age at which a record is considered stale.

        Returns:
            int: Number of stale upload records.
        """
        statement = select(func.count(Upload.id)).where(
            Upload.last_updated_at < self._stale_cutoff(older_than)
        )
        with db as session:
            return session.scalar(statement) or 0

    def delete_stale(self, db: Session, older_than: timedelta) -> int:
        """Purge upload records that have aged past the retention window.

        Args:
            db (Session): Database session.
            older_than (timedelta): Age at which a record is considered stale.

        Returns:
            int: Number of rows deleted.
        """
        statement = delete(Upload).where(
            Upload.last_updated_at < self._stale_cutoff(older_than)
        )
        with db as session:
            result = cast("CursorResult[Any]", session.execute(statement))
            session.commit()
        return result.rowcount

    @staticmethod
    def _stale_cutoff(older_than: timedelta) -> datetime:
        """Get the oldest timestamp still inside the retention window.

        Args:
            older_than (timedelta): Age at which a record is considered stale.

        Returns:
            datetime: Cutoff timestamp.
        """
        return datetime.now(timezone.utc) - older_than


upload = CRUDUpload(Upload)
