from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from geojson_pydantic import Feature
from pydantic import BaseModel, ConfigDict, Field, UUID4


if TYPE_CHECKING:
    from app.schemas.annotation_attachment import AnnotationAttachment
    from app.schemas.annotation_tag import AnnotationTag
    from app.schemas.data_product import DataProduct
    from app.schemas.user import User


# shared properties
class AnnotationBase(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1)
    geom: Optional[Feature] = None


# properties to receive via API on creation
class AnnotationCreate(AnnotationBase):
    description: str = Field(min_length=1)
    geom: Feature


# properties to receive via API on update
class AnnotationUpdate(AnnotationBase):
    pass


# properties shared by models stored in DB
class AnnotationInDBBase(AnnotationBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID4
    description: str
    # Map ORM attribute "feature_geojson" into response field "geom"
    geom: Feature = Field(validation_alias="feature_geojson")
    data_product_id: UUID4
    created_by_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime


# additional properties to return via API
class Annotation(AnnotationInDBBase):
    attachments: List["AnnotationAttachment"] = []
    created_by: Optional["User"] = None
    data_product: Optional["DataProduct"] = None
    tag_rows: List["AnnotationTag"] = []


# additional properties stored in DB
class AnnotationInDB(AnnotationInDBBase):
    pass
