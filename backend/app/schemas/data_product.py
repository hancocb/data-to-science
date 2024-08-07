from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel

from app.utils.ImageProcessor import STACProperties


# shared properties
class DataProductBase(BaseModel):
    data_type: Optional[str] = None
    filepath: Optional[str] = None
    original_filename: Optional[str] = None
    stac_properties: Optional[STACProperties] = None
    is_active: bool = True
    is_initial_processing_completed: bool = False


# properties to receive via API on creation
class DataProductCreate(DataProductBase):
    data_type: str
    filepath: str
    original_filename: str
    stac_properties: Optional[STACProperties] = None


# properties to receive via API on update
class DataProductUpdate(DataProductBase):
    pass


# properties shared by models stored in DB
class DataProductInDBBase(DataProductBase, from_attributes=True):
    id: UUID
    data_type: str
    filepath: str
    flight_id: UUID
    original_filename: str
    stac_properties: Optional[STACProperties] = None
    user_style: Optional[dict] = None
    is_active: bool
    is_initial_processing_completed: bool
    deactivated_at: Optional[datetime] = None


# additional properties to return via API
class DataProduct(DataProductInDBBase):
    public: bool = False
    status: Optional[str] = None
    url: Optional[AnyHttpUrl] = None


# additional properties stored in DB
class DataProductInDB(DataProductInDBBase):
    pass
