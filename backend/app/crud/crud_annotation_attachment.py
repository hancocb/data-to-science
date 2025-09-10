from app.crud.base import CRUDBase
from app.models.annotation_attachment import AnnotationAttachment
from app.schemas.annotation_attachment import (
    AnnotationAttachmentCreate,
    AnnotationAttachmentUpdate,
)


class CRUDAnnotationAttachment(
    CRUDBase[
        AnnotationAttachment, AnnotationAttachmentCreate, AnnotationAttachmentUpdate
    ]
):
    pass


annotation_attachment = CRUDAnnotationAttachment(AnnotationAttachment)
