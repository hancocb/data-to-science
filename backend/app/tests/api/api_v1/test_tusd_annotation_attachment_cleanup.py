"""Tests for what an annotation attachment leaves on the tusd server.

Attachments are moved into place while the hook runs instead of being handed to
a task, so this is the only chance to remove the upload's .info file and to take
the attachment back off disk if nothing ends up pointing at it.
"""

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.tests.utils.annotation import create_annotation
from app.tests.utils.data_product import SampleDataProduct


def build_attachment_post_finish_payload(
    *,
    upload_id: str,
    storage_path: str,
    project_id: str,
    flight_id: str,
    data_product_id: str,
    annotation_id: str,
    filename: str,
    info_path: str | None = None,
) -> dict:
    """Build a tusd post-finish hook payload for an annotation attachment."""
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
                    "Cookie": [],
                    "Host": ["localhost"],
                    "Origin": ["http://localhost"],
                    "Tus-Resumable": ["1.0.0"],
                    "User-Agent": ["test"],
                    "X-Forwarded-Host": ["localhost"],
                    "X-Forwarded-Proto": ["http"],
                    "X-Project-Id": [project_id],
                    "X-Flight-Id": [flight_id],
                    "X-Data-Type": ["annotation_attachment"],
                    "X-Annotation-Id": [annotation_id],
                    "X-Data-Product-Id": [data_product_id],
                },
            },
        },
    }


def store_upload(tmp_path: Path, upload_id: str) -> tuple[Path, Path]:
    """Write the two files tusd holds for a finished upload."""
    data_path = tmp_path / upload_id
    data_path.write_bytes(b"attachment bytes")
    info_path = tmp_path / f"{upload_id}.info"
    info_path.write_text("{}")
    return data_path, info_path


def get_attachment_dir(
    project_id: UUID, flight_id: UUID, data_product_id: UUID, annotation_id: UUID
) -> Path:
    """Build the static directory an annotation's attachments are served from."""
    return (
        Path(settings.TEST_STATIC_DIR)
        / "projects"
        / str(project_id)
        / "flights"
        / str(flight_id)
        / "data_products"
        / str(data_product_id)
        / "annotations"
        / str(annotation_id)
    )


def test_attachment_upload_is_removed_from_tusd(
    client: TestClient, db: Session, tmp_path: Path
) -> None:
    """A stored attachment leaves neither of its tusd files behind."""
    data_product = SampleDataProduct(db)
    annotation = create_annotation(
        db, data_product_id=data_product.obj.id, created_by_id=data_product.user.id
    )
    upload_id = uuid4().hex
    data_path, info_path = store_upload(tmp_path, upload_id)

    payload = build_attachment_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        project_id=str(data_product.project.id),
        flight_id=str(data_product.flight.id),
        data_product_id=str(data_product.obj.id),
        annotation_id=str(annotation.id),
        filename="photo.jpg",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert not data_path.exists()
    assert not info_path.exists()

    attachments = crud.annotation_attachment.get_multi_by_annotation_id(
        db, annotation_id=annotation.id
    )
    assert len(attachments) == 1
    attachment_dir = get_attachment_dir(
        data_product.project.id,
        data_product.flight.id,
        data_product.obj.id,
        annotation.id,
    )
    assert len(list(attachment_dir.iterdir())) == 1


def test_attachment_with_an_unsupported_extension_is_removed_from_tusd(
    client: TestClient, db: Session, tmp_path: Path
) -> None:
    """A refused attachment is not left on the tus server."""
    data_product = SampleDataProduct(db)
    annotation = create_annotation(
        db, data_product_id=data_product.obj.id, created_by_id=data_product.user.id
    )
    upload_id = uuid4().hex
    data_path, info_path = store_upload(tmp_path, upload_id)

    payload = build_attachment_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        project_id=str(data_product.project.id),
        flight_id=str(data_product.flight.id),
        data_product_id=str(data_product.obj.id),
        annotation_id=str(annotation.id),
        filename="elevation.tif",
    )

    response = client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not data_path.exists()
    assert not info_path.exists()
    assert (
        crud.annotation_attachment.get_multi_by_annotation_id(
            db, annotation_id=annotation.id
        )
        == []
    )


def test_attachment_is_removed_when_its_record_cannot_be_created(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An attachment nothing points at is taken back off disk."""
    data_product = SampleDataProduct(db)
    annotation = create_annotation(
        db, data_product_id=data_product.obj.id, created_by_id=data_product.user.id
    )
    upload_id = uuid4().hex
    data_path, info_path = store_upload(tmp_path, upload_id)

    def fail(*args, **kwargs) -> None:
        raise RuntimeError("database is down")

    monkeypatch.setattr(crud.annotation_attachment, "create_with_annotation", fail)

    payload = build_attachment_post_finish_payload(
        upload_id=upload_id,
        storage_path=str(data_path),
        project_id=str(data_product.project.id),
        flight_id=str(data_product.flight.id),
        data_product_id=str(data_product.obj.id),
        annotation_id=str(annotation.id),
        filename="photo.jpg",
    )

    with pytest.raises(RuntimeError):
        client.post(f"{settings.API_V1_STR}/tusd", json=payload)

    attachment_dir = get_attachment_dir(
        data_product.project.id,
        data_product.flight.id,
        data_product.obj.id,
        annotation.id,
    )
    assert list(attachment_dir.iterdir()) == []
    assert not data_path.exists()
    assert not info_path.exists()
