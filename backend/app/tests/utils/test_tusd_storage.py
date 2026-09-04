"""Tests for the helpers that remove uploads from tusd storage."""

from pathlib import Path

import pytest

from app.utils.tusd.storage import (
    get_info_path,
    remove_upload_from_tusd,
    removes_tusd_upload,
)

UPLOAD_ID = "0" * 32


def create_upload(upload_dir: Path, upload_id: str = UPLOAD_ID) -> tuple[Path, Path]:
    """Write the two files tusd stores for an upload."""
    data_path = upload_dir / upload_id
    info_path = upload_dir / f"{upload_id}.info"
    data_path.write_bytes(b"uploaded bytes")
    info_path.write_text("{}")
    return data_path, info_path


def test_get_info_path_falls_back_to_the_filestore_name(tmp_path: Path) -> None:
    """Older hook payloads do not report the .info file's location."""
    data_path = tmp_path / UPLOAD_ID

    assert get_info_path(data_path) == tmp_path / f"{UPLOAD_ID}.info"


def test_remove_upload_removes_data_and_info(tmp_path: Path) -> None:
    """Both of the files tusd wrote are removed."""
    data_path, info_path = create_upload(tmp_path)

    assert remove_upload_from_tusd(data_path) is True
    assert not data_path.exists()
    assert not info_path.exists()


def test_remove_upload_accepts_files_that_are_already_gone(tmp_path: Path) -> None:
    """Removing an upload twice is not a failure."""
    data_path, _ = create_upload(tmp_path)
    remove_upload_from_tusd(data_path)

    assert remove_upload_from_tusd(data_path) is True


def test_remove_upload_uses_the_info_path_tusd_reported(tmp_path: Path) -> None:
    """The .info file is not assumed to sit next to the uploaded bytes."""
    data_path, _ = create_upload(tmp_path)
    info_path = tmp_path / "elsewhere.info"
    info_path.write_text("{}")

    assert remove_upload_from_tusd(data_path, str(info_path)) is True
    assert not data_path.exists()
    assert not info_path.exists()


def test_remove_upload_refuses_a_directory(tmp_path: Path) -> None:
    """A directory is not an upload, so it is reported instead of removed."""
    directory = tmp_path / UPLOAD_ID
    directory.mkdir()
    (directory / "keep.txt").write_text("keep")

    assert remove_upload_from_tusd(directory) is False
    assert (directory / "keep.txt").exists()


def test_decorator_removes_upload_when_task_returns(tmp_path: Path) -> None:
    """A task that finishes leaves nothing on the tusd server."""
    data_path, info_path = create_upload(tmp_path)

    @removes_tusd_upload
    def task(storage_path: str) -> str:
        return "done"

    assert task(str(data_path)) == "done"
    assert not data_path.exists()
    assert not info_path.exists()


def test_decorator_removes_upload_when_task_raises(tmp_path: Path) -> None:
    """A task that fails leaves nothing on the tusd server either."""
    data_path, info_path = create_upload(tmp_path)

    @removes_tusd_upload
    def task(storage_path: str) -> None:
        raise RuntimeError("processing failed")

    with pytest.raises(RuntimeError):
        task(str(data_path))

    assert not data_path.exists()
    assert not info_path.exists()


def test_decorator_finds_storage_path_passed_by_keyword(tmp_path: Path) -> None:
    """Tasks are called with positional args, but the name is what matters."""
    data_path, info_path = create_upload(tmp_path)

    @removes_tusd_upload
    def task(job_id: int, storage_path: str) -> None:
        return None

    task(job_id=1, storage_path=str(data_path))

    assert not data_path.exists()
    assert not info_path.exists()
