"""Tests for the sweep that removes uploads left on the tusd server.

An upload that is still being uploaded can be resumed by its client, so it is
kept for a week. One that finished only has to outlast the task that copies it
into the user data volume, so it is kept for a day.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import crud
from app.models.upload import Upload
from app.tests.utils.user import create_user
from app.utils.cleanup.cleanup_main import get_parser, run
from app.utils.cleanup.cleanup_tusd_uploads import cleanup_tusd_uploads
from app.utils.tusd.storage import get_tusd_upload_dir

UPLOADED_BYTES = b"uploaded bytes"


def store_upload(
    upload_dir: Path,
    complete: bool = False,
    with_data: bool = True,
    with_info: bool = True,
    info_text: Optional[str] = None,
) -> tuple[str, Path, Path]:
    """Write the files tusd holds for one upload.

    Args:
        upload_dir (Path): Directory tusd writes uploads to.
        complete (bool): Write an .info file reporting the size already stored.
        with_data (bool): Write the file holding the uploaded bytes.
        with_info (bool): Write the .info file.
        info_text (Optional[str]): Contents for the .info file.

    Returns:
        tuple[str, Path, Path]: Upload id and the paths of its two files.
    """
    upload_id = uuid4().hex
    data_path = upload_dir / upload_id
    info_path = upload_dir / f"{upload_id}.info"

    if with_data:
        data_path.write_bytes(UPLOADED_BYTES)
    if with_info:
        if info_text is None:
            size = len(UPLOADED_BYTES) if complete else len(UPLOADED_BYTES) * 10
            info_text = json.dumps({"ID": upload_id, "Size": size})
        info_path.write_text(info_text)

    return upload_id, data_path, info_path


def backdate(*paths: Path, days: float) -> None:
    """Move files' modified times back so they age out of a retention window."""
    when = time.time() - days * 86400
    for path in paths:
        if path.exists():
            os.utime(path, (when, when))


def backdate_upload_record(db: Session, upload_id: UUID, days: float) -> None:
    """Move an upload record's last update far enough back to be removed."""
    with db as session:
        session.execute(
            update(Upload)
            .where(Upload.id == upload_id)
            .values(
                last_updated_at=datetime.now(tz=timezone.utc) - timedelta(days=days)
            )
        )
        session.commit()


def record_exists(db: Session, upload_id: UUID) -> bool:
    """Check whether an upload record is still in the database."""
    with db as session:
        return (
            session.scalar(select(Upload.id).where(Upload.id == upload_id)) is not None
        )


def test_incomplete_upload_inside_the_resume_window_is_kept(
    db: Session, tmp_path: Path
) -> None:
    """A paused upload is left where its client can still resume it."""
    _, data_path, info_path = store_upload(tmp_path)
    backdate(data_path, info_path, days=3)

    stats = cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert stats["items_removed"] == 0
    assert stats["items_skipped"] == 1
    assert data_path.exists()
    assert info_path.exists()


def test_incomplete_upload_past_the_resume_window_is_removed(
    db: Session, tmp_path: Path
) -> None:
    """An upload nobody came back for is not kept forever."""
    upload_id, data_path, info_path = store_upload(tmp_path)
    backdate(data_path, info_path, days=8)

    stats = cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert stats["items_removed"] == 1
    assert stats["failures"] == 0
    assert stats["space_freed_up"] > 0
    assert stats["removed_ids"] == {upload_id}
    assert not data_path.exists()
    assert not info_path.exists()


def test_completed_upload_is_removed_once_its_task_has_had_time_to_run(
    db: Session, tmp_path: Path
) -> None:
    """A finished upload that was never processed cannot be resumed."""
    _, data_path, info_path = store_upload(tmp_path, complete=True)
    backdate(data_path, info_path, days=2)

    stats = cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert stats["items_removed"] == 1
    assert not data_path.exists()
    assert not info_path.exists()


def test_completed_upload_is_kept_while_its_task_could_still_be_running(
    db: Session, tmp_path: Path
) -> None:
    """Removing an upload out from under the task copying it would fail it."""
    _, data_path, info_path = store_upload(tmp_path, complete=True)
    backdate(data_path, info_path, days=0.25)

    stats = cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert stats["items_removed"] == 0
    assert stats["items_skipped"] == 1
    assert data_path.exists()


def test_upload_with_a_deferred_size_is_kept_for_the_resume_window(
    db: Session, tmp_path: Path
) -> None:
    """Without a size there is no way to tell the upload finished."""
    _, data_path, info_path = store_upload(
        tmp_path, info_text=json.dumps({"Size": None, "SizeIsDeferred": True})
    )
    backdate(data_path, info_path, days=2)

    stats = cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert stats["items_skipped"] == 1
    assert data_path.exists()


def test_upload_with_an_unreadable_info_file_is_kept_for_the_resume_window(
    db: Session, tmp_path: Path
) -> None:
    """An .info file that cannot be parsed is not evidence the upload finished."""
    _, data_path, info_path = store_upload(tmp_path, info_text="not json")
    backdate(data_path, info_path, days=2)

    stats = cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert stats["items_skipped"] == 1
    assert data_path.exists()


def test_half_of_an_upload_is_removed_like_a_finished_one(
    db: Session, tmp_path: Path
) -> None:
    """One file without the other cannot be resumed or processed."""
    _, data_path, _ = store_upload(tmp_path, with_info=False)
    _, _, info_path = store_upload(tmp_path, with_data=False)
    backdate(data_path, info_path, days=2)

    stats = cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert stats["items_removed"] == 2
    assert not data_path.exists()
    assert not info_path.exists()


def test_files_that_are_not_uploads_are_left_alone(db: Session, tmp_path: Path) -> None:
    """Only files named the way tusd names an upload are ever removed."""
    unrelated = tmp_path / "notes.txt"
    unrelated.write_text("not an upload")
    short_name = tmp_path / ("a" * 31)
    short_name.write_text("not an upload id")
    directory = tmp_path / uuid4().hex
    directory.mkdir()
    (directory / "keep.txt").write_text("keep")
    backdate(unrelated, short_name, directory, days=30)

    stats = cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert stats["items_removed"] == 0
    assert stats["failures"] == 0
    assert unrelated.exists()
    assert short_name.exists()
    assert (directory / "keep.txt").exists()


def test_check_only_reports_what_it_would_remove_without_removing_it(
    db: Session, tmp_path: Path
) -> None:
    """A dry run reports the same totals as the run that removes the files."""
    _, data_path, info_path = store_upload(tmp_path)
    backdate(data_path, info_path, days=8)

    dry_run = cleanup_tusd_uploads(db, check_only=True, upload_dir=tmp_path)

    assert data_path.exists()
    assert info_path.exists()

    real_run = cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert not data_path.exists()
    assert dry_run["items_removed"] == real_run["items_removed"]
    assert dry_run["space_freed_up"] == real_run["space_freed_up"]
    assert dry_run["removed_ids"] == real_run["removed_ids"]


def test_missing_upload_directory_reports_nothing(db: Session, tmp_path: Path) -> None:
    """A deployment without tusd storage mounted is not a failure."""
    stats = cleanup_tusd_uploads(db, upload_dir=tmp_path / "missing")

    assert stats["items_removed"] == 0
    assert stats["items_skipped"] == 0
    assert stats["failures"] == 0


def test_upload_records_past_the_retention_window_are_removed(
    db: Session, tmp_path: Path
) -> None:
    """Records outlive the uploads they track, so they are pruned as well."""
    user = create_user(db)
    stale = crud.upload.create_with_user(db, upload_id=uuid4().hex, user_id=user.id)
    recent = crud.upload.create_with_user(db, upload_id=uuid4().hex, user_id=user.id)
    backdate_upload_record(db, stale.id, days=8)

    cleanup_tusd_uploads(db, upload_dir=tmp_path)

    assert not record_exists(db, stale.id)
    assert record_exists(db, recent.id)


def test_check_only_keeps_upload_records(db: Session, tmp_path: Path) -> None:
    """A dry run reports the records it would remove and leaves them in place."""
    user = create_user(db)
    stale = crud.upload.create_with_user(db, upload_id=uuid4().hex, user_id=user.id)
    backdate_upload_record(db, stale.id, days=8)

    cleanup_tusd_uploads(db, check_only=True, upload_dir=tmp_path)

    assert record_exists(db, stale.id)


def test_cleanup_run_sweeps_the_tusd_upload_directory(db: Session) -> None:
    """The cleanup utility reaches the real upload directory unless skipped."""
    upload_dir = get_tusd_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    _, data_path, info_path = store_upload(upload_dir)
    backdate(data_path, info_path, days=8)

    skipped = run(db, get_parser().parse_args(["--skip-tusd-uploads"]))

    assert "Tusd uploads" not in skipped
    assert data_path.exists()

    results = run(db, get_parser().parse_args([]))

    assert results["Tusd uploads"]["items_removed"] == 1
    assert not data_path.exists()
    assert not info_path.exists()
