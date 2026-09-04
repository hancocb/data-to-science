"""Tests for the extension check that runs before tusd stores an upload.

Pre-create is the only blocking hook, so an unsupported file has to be refused
here. Catching it later leaves the whole upload on the tus server with nothing
that will ever process it.
"""

from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.flight import create_flight
from app.tests.utils.indoor_project import create_indoor_project
from app.tests.utils.project import create_project


def build_pre_create_payload(
    *,
    access_token: str,
    filename: str,
    project_id: str | None = None,
    flight_id: str | None = None,
    data_type: str | None = None,
    indoor_project_id: str | None = None,
) -> dict:
    """Build a tusd pre-create hook payload for an upload named filename."""
    return {
        "Type": "pre-create",
        "Event": {
            "Upload": {
                "ID": uuid4().hex,
                "Size": 1024,
                "SizeIsDeferred": False,
                "Offset": 0,
                "MetaData": {
                    "filename": filename,
                    "filetype": "application/octet-stream",
                    "name": filename,
                    "relativePath": "null",
                    "type": "application/octet-stream",
                },
                "IsPartial": False,
                "IsFinal": False,
                "PartialUploads": None,
                "Storage": None,
            },
            "HTTPRequest": {
                "Method": "POST",
                "URI": "/files/",
                "RemoteAddr": "127.0.0.1",
                "Header": {
                    "Accept": ["*/*"],
                    "Accept-Encoding": ["gzip"],
                    "Accept-Language": ["en-US"],
                    "Connection": ["keep-alive"],
                    "Cookie": [f"access_token=Bearer {access_token}"],
                    "Host": ["localhost"],
                    "Origin": ["http://localhost"],
                    "Tus-Resumable": ["1.0.0"],
                    "User-Agent": ["test"],
                    "X-Forwarded-Host": ["localhost"],
                    "X-Forwarded-Proto": ["http"],
                    **({"X-Project-Id": [project_id]} if project_id else {}),
                    **({"X-Flight-Id": [flight_id]} if flight_id else {}),
                    **({"X-Data-Type": [data_type]} if data_type else {}),
                    **(
                        {"X-Indoor-Project-Id": [indoor_project_id]}
                        if indoor_project_id
                        else {}
                    ),
                },
            },
        },
    }


def assert_rejected(response) -> None:
    """Check tusd was told to refuse the upload with a 400."""
    assert response.status_code == status.HTTP_202_ACCEPTED
    body = response.json()
    assert body["RejectUpload"] is True
    assert body["HTTPResponse"]["StatusCode"] == status.HTTP_400_BAD_REQUEST


SUPPORTED = [
    ("dsm", "elevation.tif"),
    ("ortho", "ORTHO.TIF"),
    ("point_cloud", "cloud.copc.laz"),
    ("point_cloud", "cloud.las"),
    ("3dgs", "scene.ply"),
    ("3dgs", "scene.zip"),
    ("raw", "images.zip"),
    ("annotation_attachment", "photo.gif"),
]

UNSUPPORTED = [
    ("dsm", "installer.exe"),
    ("dsm", "notes.txt"),
    ("point_cloud", "cloud.e57"),
    ("raw", "images.tar"),
    ("annotation_attachment", "elevation.tif"),
]


@pytest.mark.parametrize("data_type,filename", SUPPORTED)
def test_pre_create_allows_a_supported_extension(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    data_type: str,
    filename: str,
) -> None:
    """Every extension a data type accepts passes the pre-create check."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)

    payload = build_pre_create_payload(
        access_token=normal_user_access_token,
        filename=filename,
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type=data_type,
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"status": "authorized"}


@pytest.mark.parametrize("data_type,filename", UNSUPPORTED)
def test_pre_create_refuses_an_unsupported_extension(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    data_type: str,
    filename: str,
) -> None:
    """An extension a data type does not accept never reaches the tus server."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)

    payload = build_pre_create_payload(
        access_token=normal_user_access_token,
        filename=filename,
        project_id=str(project.id),
        flight_id=str(flight.id),
        data_type=data_type,
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert_rejected(response)


@pytest.mark.parametrize("filename", ["counts.xlsx", "counts.xls", "scans.tar"])
def test_pre_create_allows_a_supported_indoor_extension(
    client: TestClient, db: Session, normal_user_access_token: str, filename: str
) -> None:
    """Indoor projects take spreadsheets and tar archives."""
    current_user = get_current_user(db, normal_user_access_token)
    indoor_project = create_indoor_project(db, owner_id=current_user.id)

    payload = build_pre_create_payload(
        access_token=normal_user_access_token,
        filename=filename,
        indoor_project_id=str(indoor_project.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {"status": "authorized"}


@pytest.mark.parametrize("filename", ["counts.zip", "elevation.tif"])
def test_pre_create_refuses_an_unsupported_indoor_extension(
    client: TestClient, db: Session, normal_user_access_token: str, filename: str
) -> None:
    """An extension the indoor pipeline cannot read is refused up front."""
    current_user = get_current_user(db, normal_user_access_token)
    indoor_project = create_indoor_project(db, owner_id=current_user.id)

    payload = build_pre_create_payload(
        access_token=normal_user_access_token,
        filename=filename,
        indoor_project_id=str(indoor_project.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert_rejected(response)
