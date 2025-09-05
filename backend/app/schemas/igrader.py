from datetime import datetime
from typing import Optional, Tuple

from pydantic import BaseModel, UUID4


DefectInts = Tuple[int, int, int, int, int, int]


# properties in POST requests
class IGraderPost(BaseModel):
    scribner_price: Optional[float] = None
    crookAngle: Optional[float] = None
    grade: Optional[str] = None
    formClass: float
    sweepAngle: float
    date_created: float
    defect_array_dim: Tuple[int, int]
    species: str
    longitude: Optional[float] = None
    treeHeight: float
    international_val: Optional[float] = None
    defects: Tuple[
        DefectInts,
        DefectInts,
        DefectInts,
        DefectInts,
    ]
    date_modified: float
    sweep: float
    latitude: Optional[float] = None
    mode: str
    dbh: float
    crookRatio: float
    scribner_val: Optional[float] = None
    buttOnly: bool
    id: UUID4
    face_images: Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]
    international_price: Optional[float] = None
    doyle_price: Optional[float] = None
    crook: float
    doyle_val: Optional[float] = None


# shared properties stored in db
class IGraderBase(BaseModel):
    pass


# properties to receive via API on creation
class IGraderCreate(IGraderBase):
    pass


# properties to receive via API on update
class IGraderUpdate(IGraderBase):
    pass


# properties shared by models stored in DB
class IGraderInDBBase(IGraderBase):
    id: UUID4
    time_stamp: datetime
    project_id: UUID4


# additional properties to return via API
class IGrader(IGraderInDBBase):
    pass


# additional properties stored in DB
class IGraderInDB(IGraderInDBBase):
    pass
