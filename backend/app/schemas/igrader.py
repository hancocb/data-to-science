from datetime import datetime
from typing import Optional

from uuid import UUID

from pydantic import BaseModel, ConfigDict


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

    id: UUID
    igrader_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    project_id: UUID


# Response schema
class IGrader(IGraderInDBBase):
    pass


# Additional properties stored in DB
class IGraderInDB(IGraderInDBBase):
    pass
