from datetime import datetime
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, UUID4

if TYPE_CHECKING:
    from app.schemas.tag import Tag


# shared properties
class AnnotationTagBase(BaseModel):
    tag_id: Optional[UUID4] = None


# properties to receive via API on creation
class AnnotationTagCreate(AnnotationTagBase):
    tag_id: UUID4


# properties to receive via API on update
class AnnotationTagUpdate(AnnotationTagBase):
    pass


# properties shared by models stored in DB
class AnnotationTagInDBBase(AnnotationTagBase, from_attributes=True):
    id: UUID4
    annotation_id: UUID4
    tag_id: UUID4
    created_at: datetime
    updated_at: datetime


# additional properties to return via API
class AnnotationTag(AnnotationTagInDBBase):
    tag: Optional["Tag"] = None


# additional properties stored in DB
class AnnotationTagInDB(AnnotationTagInDBBase):
    pass
