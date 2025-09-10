from app.crud.base import CRUDBase
from app.models.annotation_tag import AnnotationTag
from app.schemas.annotation_tag import AnnotationTagCreate, AnnotationTagUpdate


class CRUDAnnotationTag(
    CRUDBase[AnnotationTag, AnnotationTagCreate, AnnotationTagUpdate]
):
    pass


annotation_tag = CRUDAnnotationTag(AnnotationTag)
