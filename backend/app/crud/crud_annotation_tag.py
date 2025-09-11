from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.annotation_tag import AnnotationTag
from app.schemas.annotation_tag import AnnotationTagCreate, AnnotationTagUpdate


class CRUDAnnotationTag(
    CRUDBase[AnnotationTag, AnnotationTagCreate, AnnotationTagUpdate]
):
    def create_with_annotation(
        self, db: Session, *, obj_in: AnnotationTagCreate, annotation_id: UUID
    ) -> AnnotationTag:
        """Create an annotation-tag relation, passing annotation_id separately.

        The provided annotation_id argument takes precedence over any value in obj_in.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = AnnotationTag(**obj_in_data, annotation_id=annotation_id)
        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
        return db_obj

    def get_multi_by_annotation_id(
        self, db: Session, annotation_id: UUID
    ) -> Sequence[AnnotationTag]:
        """Return all annotation-tag rows for a given annotation."""
        statement = select(AnnotationTag).where(
            AnnotationTag.annotation_id == annotation_id
        )
        with db as session:
            return session.scalars(statement).all()


annotation_tag = CRUDAnnotationTag(AnnotationTag)
