"""Tests for what post-finish does with an upload it refuses to process.

post-finish is not a blocking hook, so tusd only logs a rejection and keeps the
upload. The upload is complete by then and cannot be resumed, so a rejection
has to remove it. A failure that tusd will retry, or one that never reached a
decision, must leave it alone.
"""

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.tests.utils.flight import create_flight
from app.tests.utils.project import create_project
from app.tests.utils.user import create_user, login_and_get_access_token


def build_post_finish_payload(
    *,
    upload_id: str,
    storage_path: str,
    cookie: list[str],
    project_id: str,
    flight_id: str,
    data_type: str = "dsm",
    filename: str = "elevation.tif",
    info_path: str | None = None,
) -> dict:
    """Build a tusd post-finish hook payload for a stored upload."""
    return {
        "Type": "post-finish",
        "Event": {
            "Upload": {
                "ID": upload_id,
                "Size": 1024,
                "SizeIsDeferred": False,
                "Offset": 1024,
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
                "Storage": {
                    "Path": storage_path,
                    "Type": "filestore",
                    **({"InfoPath": info_path} if info_path else {}),
                },
            },
            "HTTPRequest": {
                "Method": "PATCH",
                "URI": "/files/",
                "RemoteAddr": "127.0.0.1",
                "Header": {
                    "Accept": ["*/*"],
                    "Accept-Encoding": ["gzip"],
                    "Accept-Language": ["en-US"],
                    "Connection": ["keep-alive"],
                    "Cookie": cookie,
                    "Host": ["localhost"],
                    "Origin": ["http://localhost"],
                    "Tus-Resumable": ["1.0.0"],
                    "User-Agent": ["test"],
                    "X-Forwarded-Host": ["localhost"],
                    "X-Forwarded-Proto": ["http"],
                    "X-Project-Id": [project_id],
                    "X-Flight-Id": [flight_id],
                    "X-Data-Type": [data_type],
                },
            },
        },
    }


def store_upload(tmp_path: Path, upload_id: str) -> tuple[Path, Path]:
    """Write the two files tusd holds for a finished upload."""
    data_path = tmp_path / upload_id
    data_path.write_bytes(b"uploaded bytes")
    info_path = tmp_path / f"{upload_id}.info"
    info_path.write_text("{}")
    return data_path, info_path


@pytest.fixture
def process_data_product_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Capture calls to the data product post-processing function."""
    calls: list[dict] = []

    def fake_process(db: Session, **kwargs) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(
        "app.api.api_v1.endpoints.tusd.process_data_product_uploaded_to_tusd",
        fake_process,
    )
    return calls


def test_post_finish_removes_an_upload_it_cannot_place(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    tmp_path: Path,
) -> None:
    """An upload for a flight that does not exist has nowhere to go."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    upload_id = uuid4().hex
    data_path, info_path = store_upload(tmp_path, upload_id)

    payload = build_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        project_id=str(project.id),
        flight_id=str(uuid4()),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert not data_path.exists()
    assert not info_path.exists()


def test_post_finish_removes_an_upload_from_a_user_without_access(
    client: TestClient, db: Session, tmp_path: Path
) -> None:
    """An upload whose owner cannot write to the project is never processed."""
    password = "SecurePassword123"
    other_user = create_user(db, password=password)
    other_token = login_and_get_access_token(
        client=client, email=other_user.email, password=password
    )
    project = create_project(db)
    flight = create_flight(db, project_id=project.id)
    upload_id = uuid4().hex
    data_path, info_path = store_upload(tmp_path, upload_id)

    payload = build_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        cookie=[f"access_token=Bearer {other_token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not data_path.exists()
    assert not info_path.exists()


def test_post_finish_removes_an_upload_it_cannot_attribute(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    tmp_path: Path,
) -> None:
    """Without a record or a token there is no user to own the upload."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex
    data_path, info_path = store_upload(tmp_path, upload_id)

    payload = build_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        cookie=[],
        project_id=str(project.id),
        flight_id=str(flight.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not data_path.exists()
    assert not info_path.exists()


def test_post_finish_removes_an_upload_with_an_unsupported_extension(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    tmp_path: Path,
) -> None:
    """A file that slipped past pre-create is removed once it is refused.

    Post processing runs for real here, so the rejection comes from the same
    check the pre-create hook uses.
    """
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex
    crud.upload.create_with_user(
        db, upload_id=upload_id, user_id=current_user.id, is_uploading=True
    )
    data_path, info_path = store_upload(tmp_path, upload_id)

    payload = build_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
        filename="notes.txt",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not data_path.exists()
    assert not info_path.exists()


def test_post_finish_removes_the_info_file_tusd_reported(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    tmp_path: Path,
) -> None:
    """The .info file is not assumed to sit next to the uploaded bytes."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    upload_id = uuid4().hex
    data_path, adjacent_info_path = store_upload(tmp_path, upload_id)
    reported_info_path = tmp_path / "elsewhere.info"
    reported_info_path.write_text("{}")

    payload = build_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        project_id=str(project.id),
        flight_id=str(uuid4()),
        info_path=str(reported_info_path),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert not data_path.exists()
    assert not reported_info_path.exists()
    assert adjacent_info_path.exists()


def test_post_finish_keeps_an_upload_after_an_unexpected_failure(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """tusd retries a 5xx, so the upload has to still be there for the retry."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex
    crud.upload.create_with_user(
        db, upload_id=upload_id, user_id=current_user.id, is_uploading=True
    )
    data_path, info_path = store_upload(tmp_path, upload_id)

    def fail(db: Session, **kwargs) -> None:
        raise RuntimeError("database is down")

    monkeypatch.setattr(
        "app.api.api_v1.endpoints.tusd.process_data_product_uploaded_to_tusd", fail
    )

    payload = build_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
    )

    with pytest.raises(RuntimeError):
        client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert data_path.exists()
    assert info_path.exists()


def test_post_finish_keeps_an_upload_it_already_dispatched(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    process_data_product_calls: list[dict],
    tmp_path: Path,
) -> None:
    """A replayed hook must not remove a file the first hook is still using."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex
    crud.upload.create_with_user(
        db, upload_id=upload_id, user_id=current_user.id, is_uploading=False
    )
    data_path, info_path = store_upload(tmp_path, upload_id)

    payload = build_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert len(process_data_product_calls) == 0
    assert data_path.exists()
    assert info_path.exists()


def test_post_finish_leaves_a_dispatched_upload_to_its_task(
    client: TestClient,
    db: Session,
    normal_user_access_token: str,
    process_data_product_calls: list[dict],
    tmp_path: Path,
) -> None:
    """The task that copies the upload is the one that removes it."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    flight = create_flight(db, project_id=project.id, pilot_id=current_user.id)
    upload_id = uuid4().hex
    crud.upload.create_with_user(
        db, upload_id=upload_id, user_id=current_user.id, is_uploading=True
    )
    data_path, info_path = store_upload(tmp_path, upload_id)

    payload = build_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        cookie=[f"access_token=Bearer {normal_user_access_token}"],
        project_id=str(project.id),
        flight_id=str(flight.id),
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert len(process_data_product_calls) == 1
    assert data_path.exists()
    assert info_path.exists()
