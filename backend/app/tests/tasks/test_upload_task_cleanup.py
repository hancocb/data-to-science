"""Tests for how the upload tasks clean up after themselves.

Every task is handed a file on the tusd server that is complete and cannot be
resumed, so it has to remove that file and its .info file however it ends, and
it must never remove anything else the tusd server is holding.
"""

import subprocess
from pathlib import Path
from typing import Iterator
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app import crud
from app.schemas.job import Status
from app.tasks.upload_tasks import (
    upload_3dgs,
    upload_geotiff,
    upload_indoor_project_data,
    upload_panoramic,
    upload_point_cloud,
    upload_raw_data,
)
from app.tests.tasks.test_upload_point_cloud import create_test_las
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.indoor_project_data import create_indoor_project_data
from app.tests.utils.job import create_job
from app.tests.utils.raw_data import SampleRawData


@pytest.fixture
def use_test_db(db: Session) -> Iterator[None]:
    """Point both database sessions the upload tasks use at the test database.

    The tasks take one for themselves and JobManager takes another when it is
    not handed one, and each comes from a different module.
    """

    def get_test_db() -> Iterator[Session]:
        yield db

    with (
        patch("app.tasks.upload_tasks.get_db", side_effect=get_test_db),
        patch("app.utils.job_manager.get_db", side_effect=get_test_db),
    ):
        yield


def setup_tusd_dir(tmp_path: Path, filename: str = "upload.ply") -> dict:
    """Create a tusd upload directory holding the upload and a second upload.

    The second upload and the loose file stand in for everything else the tusd
    server is holding while one upload is processed.
    """
    tusd_dir = tmp_path / "tusd" / "data"
    tusd_dir.mkdir(parents=True)

    storage_path = tusd_dir / filename
    storage_path.write_bytes(b"uploaded bytes")
    info_path = tusd_dir / f"{filename}.info"
    info_path.write_text("{}")

    other_upload = tusd_dir / "another-upload"
    other_upload.write_bytes(b"someone else's upload")
    unrelated_file = tusd_dir.parent / "unrelated.txt"
    unrelated_file.write_text("not an upload")

    return {
        "storage_path": storage_path,
        "info_path": info_path,
        "other_upload": other_upload,
        "unrelated_file": unrelated_file,
    }


def setup_destination(tmp_path: Path, filename: str = "upload.ply") -> Path:
    """Create the per-upload directory a task copies its upload into."""
    work_dir = tmp_path / "data_product" / "tmp"
    work_dir.mkdir(parents=True)
    return work_dir / filename


def assert_upload_removed(tusd: dict) -> None:
    """Check the upload is gone and nothing else on the server was touched."""
    assert not tusd["storage_path"].exists()
    assert not tusd["info_path"].exists()
    assert tusd["other_upload"].exists()
    assert tusd["unrelated_file"].exists()


def test_upload_3dgs_missing_job_only_removes_its_own_upload(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """A missing job must not take the rest of the tusd volume with it.

    The task used to remove the parent of the parent of the uploaded file,
    which is the upload directory itself.
    """
    tusd = setup_tusd_dir(tmp_path)
    destination = setup_destination(tmp_path)

    assert (
        upload_3dgs(str(tusd["storage_path"]), str(destination), uuid4(), uuid4())
        is None
    )

    assert_upload_removed(tusd)


def test_upload_panoramic_missing_job_only_removes_its_own_upload(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """Same regression as the 3DGS task, which this one was copied from."""
    tusd = setup_tusd_dir(tmp_path, filename="upload.jpg")
    destination = setup_destination(tmp_path, filename="upload.jpg")

    assert (
        upload_panoramic(str(tusd["storage_path"]), str(destination), uuid4(), uuid4())
        is None
    )

    assert_upload_removed(tusd)


def test_upload_3dgs_invalid_image_removes_upload(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """An upload rejected by validation is not left on the tusd server."""
    data_product = SampleDataProduct(db, data_type="3dgs")
    tusd = setup_tusd_dir(tmp_path)
    destination = setup_destination(tmp_path)

    with patch(
        "app.tasks.upload_tasks.validate_3dgs_image",
        return_value=(False, "not a ply file"),
    ):
        upload_3dgs(
            str(tusd["storage_path"]),
            str(destination),
            data_product.job.id,
            data_product.obj.id,
        )

    assert_upload_removed(tusd)
    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED


def test_upload_geotiff_processing_failure_removes_upload(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """A GeoTIFF that cannot be processed is not left on the tusd server."""
    data_product = SampleDataProduct(db, data_type="dsm")
    tusd = setup_tusd_dir(tmp_path, filename="upload.tif")
    destination = setup_destination(tmp_path, filename="upload.tif")

    with patch(
        "app.tasks.upload_tasks.ImageProcessor", side_effect=RuntimeError("bad raster")
    ):
        upload_geotiff(
            str(tusd["storage_path"]),
            str(destination),
            data_product.user.id,
            data_product.job.id,
            data_product.obj.id,
        )

    assert_upload_removed(tusd)
    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED


def test_upload_geotiff_missing_data_product_removes_upload(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """A job without its data product still cleans up the tusd server."""
    data_product = SampleDataProduct(db, data_type="dsm")
    tusd = setup_tusd_dir(tmp_path, filename="upload.tif")
    destination = setup_destination(tmp_path, filename="upload.tif")

    upload_geotiff(
        str(tusd["storage_path"]),
        str(destination),
        data_product.user.id,
        data_product.job.id,
        uuid4(),
    )

    assert_upload_removed(tusd)
    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED


def test_upload_point_cloud_conversion_failure_removes_upload(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """A point cloud that will not convert is not left on the tusd server."""
    data_product = SampleDataProduct(db, data_type="point_cloud")
    tusd = setup_tusd_dir(tmp_path, filename="upload.las")
    create_test_las(tusd["storage_path"])
    destination = setup_destination(tmp_path, filename="upload.las")

    crashed = subprocess.CompletedProcess(
        args=["untwine"], returncode=134, stdout="", stderr="assertion failed"
    )
    with patch("app.tasks.upload_tasks.subprocess.run", return_value=crashed):
        upload_point_cloud(
            str(tusd["storage_path"]),
            str(destination),
            data_product.job.id,
            data_product.obj.id,
        )

    assert_upload_removed(tusd)
    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED


def test_upload_point_cloud_success_removes_info_file(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """A successful upload removes the .info file along with the point cloud."""
    data_product = SampleDataProduct(db, data_type="point_cloud")
    tusd = setup_tusd_dir(tmp_path, filename="upload.las")
    create_test_las(tusd["storage_path"])
    destination = setup_destination(tmp_path, filename="upload.las")

    upload_point_cloud(
        str(tusd["storage_path"]),
        str(destination),
        data_product.job.id,
        data_product.obj.id,
    )

    assert_upload_removed(tusd)
    job_in_db = crud.job.get(db, id=data_product.job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.SUCCESS


def test_upload_raw_data_missing_record_fails_job_and_removes_upload(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """Raw data whose record is gone leaves neither a stuck job nor an upload."""
    job = create_job(db, name="upload-raw-data")
    tusd = setup_tusd_dir(tmp_path, filename="upload.zip")
    destination = setup_destination(tmp_path, filename="upload.zip")

    upload_raw_data(
        uuid4(),
        str(tusd["storage_path"]),
        str(destination),
        job.id,
        uuid4(),
        uuid4(),
    )

    assert_upload_removed(tusd)
    job_in_db = crud.job.get(db, id=job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED


def test_upload_raw_data_copy_failure_removes_upload(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """Raw data that cannot be copied to static files is still cleaned up."""
    raw_data = SampleRawData(db)
    job = create_job(db, name="upload-raw-data", raw_data_id=raw_data.obj.id)
    tusd = setup_tusd_dir(tmp_path, filename="upload.zip")
    # a destination directory that does not exist fails the copy
    destination = tmp_path / "missing" / "upload.zip"

    upload_raw_data(
        raw_data.obj.id,
        str(tusd["storage_path"]),
        str(destination),
        job.id,
        raw_data.project.id,
        raw_data.user.id,
    )

    assert_upload_removed(tusd)
    job_in_db = crud.job.get(db, id=job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED


def test_upload_indoor_project_data_copy_failure_removes_upload(
    db: Session, tmp_path: Path, use_test_db: None
) -> None:
    """Indoor data that cannot be copied to static files is still cleaned up."""
    indoor_project_data = create_indoor_project_data(db)
    job = create_job(db, name="upload-indoor-data")
    tusd = setup_tusd_dir(tmp_path, filename="upload.xlsx")
    destination = tmp_path / "missing" / "upload.xlsx"

    upload_indoor_project_data(
        indoor_project_data.id,
        str(tusd["storage_path"]),
        str(destination),
        job.id,
    )

    assert_upload_removed(tusd)
    job_in_db = crud.job.get(db, id=job.id)
    assert job_in_db is not None
    assert job_in_db.status == Status.FAILED
