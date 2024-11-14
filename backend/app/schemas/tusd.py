from typing import Dict, List, Optional

from pydantic import BaseModel, Field, UUID4


class Storage(BaseModel):
    Path: str
    Type: str


class MetaData(BaseModel):
    filename: str
    filetype: str
    name: str
    relativePath: str
    type: str


class Upload(BaseModel):
    ID: str
    Size: int
    SizeIsDeferred: bool
    Offset: int
    MetaData: MetaData
    IsPartial: bool
    IsFinal: bool
    PartialUploads: None
    Storage: Storage | None


class Header(BaseModel):
    Accept: List[str]
    Accept_Encoding: List[str] = Field(alias="Accept-Encoding")
    Accept_Language: List[str] = Field(alias="Accept-Language")
    Connection: List[str]
    Content_Length: List[str] = Field(alias="Content-Length")
    Content_Type: Optional[List[str]] = Field(alias="Content-Type", default=None)
    Cookie: List[str]
    Dnt: Optional[List[str]] = None
    Host: List[str]
    Origin: List[str]
    Referer: Optional[List[str]] = None
    Sec_Fetch_Dest: Optional[List[str]] = Field(alias="Sec-Fetch-Dest", default=None)
    Sec_Fetch_Mode: Optional[List[str]] = Field(alias="Sec-Fetch-Mode", default=None)
    Sec_Fetch_Site: Optional[List[str]] = Field(alias="Sec-Fetch-Site", default=None)
    Tus_Resumable: List[str] = Field(alias="Tus-Resumable")
    Upload_Length: Optional[List[str]] = Field(alias="Upload-Length", default=None)
    Upload_Metadata: Optional[List[str]] = Field(alias="Upload-Metadata", default=None)
    Upload_Offset: Optional[List[str]] = Field(alias="Upload-Offset", default=None)
    User_Agent: List[str] = Field(alias="User-Agent")
    X_Forwarded_Host: List[str] = Field(alias="X-Forwarded-Host")
    X_Forwarded_Proto: List[str] = Field(alias="X-Forwarded-Proto")
    # custom headers
    X_Project_ID: Optional[List[UUID4]] = Field(alias="X-Project-Id", default=None)
    X_Flight_ID: Optional[List[UUID4]] = Field(alias="X-Flight-Id", default=None)
    X_Data_Type: Optional[List[str]] = Field(alias="X-Data-Type", default=None)
    X_Indoor_Project_ID: Optional[List[UUID4]] = Field(
        alias="X-Indoor-Project-Id", default=None
    )


class HTTPRequest(BaseModel):
    Method: str
    URI: str
    RemoteAddr: str
    Header: Header


class Event(BaseModel):
    Upload: Upload
    HTTPRequest: HTTPRequest


class TUSDHook(BaseModel):
    Type: str
    Event: Event
