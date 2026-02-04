from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, UUID4


# Minimal schema for POST - accepts any JSON
class IGraderPost(BaseModel):
    model_config = ConfigDict(extra="allow")


# Shared properties for DB storage
class IGraderBase(BaseModel):
    data: dict


# Properties for creation
class IGraderCreate(IGraderBase):
    pass


# Properties for update
class IGraderUpdate(BaseModel):
    data: Optional[dict] = None


# Properties shared by models stored in DB
class IGraderInDBBase(IGraderBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    created_at: datetime
    project_id: UUID4


# Response schema
class IGrader(IGraderInDBBase):
    pass


# Additional properties stored in DB
class IGraderInDB(IGraderInDBBase):
    pass
