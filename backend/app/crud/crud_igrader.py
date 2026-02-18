from typing import Optional, Sequence

from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.igrader import IGrader
from app.schemas.igrader import IGraderCreate, IGraderPost, IGraderUpdate


class CRUDIGrader(CRUDBase[IGrader, IGraderCreate, IGraderUpdate]):
    def create_or_update_from_post(
        self, db: Session, post_data: IGraderPost, project_id: UUID4
    ) -> tuple[IGrader, bool]:
        """Upsert an IGrader record from external POST data.

        If a record with the payload's "id" already exists for the
        project, update it. Otherwise, create a new record.

        Returns a tuple of (record, created) where created is True
        if a new record was inserted.
        """
        data_dict = post_data.model_dump()
        igrader_id = data_dict["id"]

        existing = self.get_by_igrader_id(
            db, igrader_id=igrader_id, project_id=project_id
        )
        if existing:
            existing.data = data_dict
            with db as session:
                session.add(existing)
                session.commit()
                session.refresh(existing)
            return existing, False

        db_obj = IGrader(
            data=data_dict,
            igrader_id=igrader_id,
            project_id=project_id,
        )
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj, True

    def get_by_igrader_id(
        self, db: Session, igrader_id: str, project_id: UUID4
    ) -> Optional[IGrader]:
        """Look up an IGrader record by the external igrader_id within a project."""
        statement = select(IGrader).where(
            IGrader.igrader_id == igrader_id,
            IGrader.project_id == project_id,
        )
        with db as session:
            return session.scalar(statement)

    def get_igrader_by_id(
        self, db: Session, igrader_id: UUID4, project_id: UUID4
    ) -> Optional[IGrader]:
        statement = select(IGrader).where(
            IGrader.id == igrader_id, IGrader.project_id == project_id
        )
        with db as session:
            igrader = session.scalar(statement)
            return igrader

    def get_multi_igrader_by_project_id(
        self, db: Session, project_id: UUID4
    ) -> Sequence[IGrader]:
        statement = select(IGrader).where(IGrader.project_id == project_id)
        with db as session:
            igraders = session.scalars(statement).all()
            return igraders

    def remove_igrader_by_id(
        self, db: Session, igrader_id: UUID4, project_id: UUID4
    ) -> Optional[IGrader]:
        igrader = self.get_igrader_by_id(
            db, igrader_id=igrader_id, project_id=project_id
        )
        if igrader:
            igrader_removed = crud.igrader.remove(db, id=igrader_id)
            return igrader_removed
        else:
            return None


igrader = CRUDIGrader(IGrader)