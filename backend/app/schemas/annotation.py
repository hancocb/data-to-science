from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from geojson_pydantic import Geometry
from pydantic import BaseModel, Field, UUID4

if TYPE_CHECKING:
    from app.schemas.annotation_attachment import AnnotationAttachment
    from app.schemas.annotation_tag import AnnotationTag
    from app.schemas.data_product import DataProduct


# shared properties
class AnnotationBase(BaseModel):
    description: Optional[str] = Field(None, min_length=1)
    geom: Optional[Geometry] = None
    data_product_id: Optional[UUID4] = None


# properties to receive via API on creation
class AnnotationCreate(AnnotationBase):
    description: str = Field(min_length=1)
    geom: Geometry
    data_product_id: UUID4


# properties to receive via API on update
class AnnotationUpdate(AnnotationBase):
    pass


# properties shared by models stored in DB
class AnnotationInDBBase(AnnotationBase, from_attributes=True):
    id: UUID4
    description: str
    geom: Geometry
    data_product_id: UUID4
    created_at: datetime
    updated_at: datetime


# additional properties to return via API
class Annotation(AnnotationInDBBase):
    data_product: Optional["DataProduct"] = None
    attachments: List["AnnotationAttachment"] = []
    tag_rows: List["AnnotationTag"] = []


# additional properties stored in DB
class AnnotationInDB(AnnotationInDBBase):
    pass
