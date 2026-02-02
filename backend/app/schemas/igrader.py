from datetime import datetime
from typing import Literal, Optional, Tuple

from pydantic import BaseModel, UUID4


DefectInts = Tuple[int, int, int, int, int, int]


# properties in POST requests
class IGraderPost(BaseModel):
    # Identity & metadata
    id: UUID4
    calculationMode: Literal["Tree", "Log"]
    mode: str
    species: str
    grade: Optional[str] = None
    date_created: float
    date_modified: float

    # Tree measurements
    dbh: float
    treeHeight: float
    formClass: float

    # Form defects
    crook: float
    crookAngle: Optional[float] = None
    crookRatio: float
    sweep: float
    sweepAngle: float
    buttOnly: bool
    defect_array_dim: Tuple[int, int]
    defects: Tuple[
        DefectInts,
        DefectInts,
        DefectInts,
        DefectInts,
    ]

    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Valuation
    doyle_val: Optional[float] = None
    doyle_price: Optional[float] = None
    international_val: Optional[float] = None
    international_price: Optional[float] = None
    scribner_val: Optional[float] = None
    scribner_price: Optional[float] = None

    # Media
    face_images: Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]


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
