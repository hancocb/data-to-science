"""Removes uploads left behind on the tusd server.

tusd stores each upload as "<id>" and "<id>.info" and never removes either one,
so an upload that is abandoned before it finishes, or that finishes but is never
processed, stays on the volume until it is removed here.
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app import crud
from app.utils.cleanup.common import new_stats
from app.utils.tusd.storage import (
    TUSD_INFO_SUFFIX,
    TUSD_UPLOAD_ID_PATTERN,
    get_tusd_upload_dir,
    remove_upload_from_tusd,
)

logger = logging.getLogger(__name__)

# An unfinished upload can still be resumed by the client that started it, so it
# is kept long enough for that to remain possible.
INCOMPLETE_RETENTION = timedelta(days=7)

# A finished upload cannot be resumed. It only has to outlast the post
# processing task that copies it to the user data volume.
COMPLETED_RETENTION = timedelta(days=1)


@dataclass
class TusdUpload:
    """An upload found in the tusd upload directory."""

    upload_id: str
    data_path: Optional[Path]
    info_path: Optional[Path]
    kind: str
    last_activity: datetime
    size: int

    @property
    def retention(self) -> timedelta:
        """Get how long this upload is kept before it can be removed."""
        if self.kind == "incomplete":
            return INCOMPLETE_RETENTION
        return COMPLETED_RETENTION


def get_expected_size(info_path: Path) -> Optional[int]:
    """Get the total size tusd recorded for an upload.

    Args:
        info_path (Path): Path to the upload's .info file.

    Returns:
        Optional[int]: Expected size in bytes, or None if it is unknown or the
            .info file cannot be read.
    """
    try:
        with open(info_path, "rb") as info_file:
            info = json.load(info_file)
    except (OSError, ValueError):
        logger.warning("Could not read tusd upload info at %s", info_path)
        return None

    if info.get("SizeIsDeferred"):
        return None
    size = info.get("Size")
    return size if isinstance(size, int) else None


def get_last_activity(paths: List[Path]) -> Optional[datetime]:
    """Get the most recent time any of an upload's files was written.

    tusd appends each chunk to the data file, so its modified time advances for
    as long as the client is still uploading.

    Args:
        paths (List[Path]): Paths belonging to a single upload.

    Returns:
        Optional[datetime]: Most recent modified time, or None if none of the
            files could be read.
    """
    modified_times = []
    for path in paths:
        try:
            modified_times.append(path.stat().st_mtime)
        except OSError:
            continue
    if not modified_times:
        return None
    return datetime.fromtimestamp(max(modified_times), tz=timezone.utc)


def scan_tusd_uploads(upload_dir: Path) -> List[TusdUpload]:
    """Find the uploads currently held on the tusd server.

    Files that are not named like a tusd upload are ignored, so anything else
    kept in the upload directory is never a candidate for removal.

    Args:
        upload_dir (Path): Directory tusd writes uploads to.

    Returns:
        List[TusdUpload]: One record per upload id found.
    """
    files: Dict[str, Dict[str, Path]] = {}
    with os.scandir(upload_dir) as entries:
        for entry in entries:
            if not entry.is_file(follow_symlinks=False):
                continue
            name = entry.name
            is_info = name.endswith(TUSD_INFO_SUFFIX)
            upload_id = name[: -len(TUSD_INFO_SUFFIX)] if is_info else name
            if not TUSD_UPLOAD_ID_PATTERN.match(upload_id):
                continue
            files.setdefault(upload_id, {})["info" if is_info else "data"] = Path(
                entry.path
            )

    uploads = []
    for upload_id, upload_files in files.items():
        data_path = upload_files.get("data")
        info_path = upload_files.get("info")
        last_activity = get_last_activity(list(upload_files.values()))
        if last_activity is None:
            # every file was removed while the directory was being scanned
            continue

        if data_path is None or info_path is None:
            kind = "orphaned"
        else:
            expected_size = get_expected_size(info_path)
            is_complete = (
                expected_size is not None and data_path.stat().st_size >= expected_size
            )
            kind = "completed" if is_complete else "incomplete"

        uploads.append(
            TusdUpload(
                upload_id=upload_id,
                data_path=data_path,
                info_path=info_path,
                kind=kind,
                last_activity=last_activity,
                size=sum(get_file_size(path) for path in upload_files.values()),
            )
        )
    return uploads


def get_file_size(path: Path) -> int:
    """Get the size of a file, or zero if it cannot be read.

    Args:
        path (Path): Path to the file.

    Returns:
        int: Size of the file in bytes.
    """
    try:
        return path.stat().st_size
    except OSError:
        return 0


def cleanup_tusd_uploads(
    db: Session,
    check_only: bool = False,
    upload_dir: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Remove uploads that the tusd server is holding on to.

    An upload that finished uploading and was processed is removed by the task
    that processed it, so anything still here either never finished or was
    never processed. Both are kept for a retention window first: an unfinished
    upload so the client can still resume it, and a finished one so a post
    processing task that is still running is not left without its source.

    Upload records for uploads that can no longer be on the server are removed
    with them, so the table does not grow without bound.

    Args:
        db (Session): Database session.
        check_only (bool): If True, report what would be removed without
            removing any files or database records.
        upload_dir (Optional[Path]): Directory tusd writes uploads to.
        now (Optional[datetime]): Time to measure the retention window from.

    Returns:
        Dict[str, Any]: Result record described by common.new_stats.
    """
    stats = new_stats()
    upload_dir = upload_dir or get_tusd_upload_dir()
    now = now or datetime.now(tz=timezone.utc)

    if not upload_dir.is_dir():
        logger.warning("Tusd upload directory %s does not exist", upload_dir)
        return stats

    for upload in scan_tusd_uploads(upload_dir):
        if now - upload.last_activity < upload.retention:
            stats["items_skipped"] += 1
            continue
        try:
            if not check_only:
                paths = [
                    path
                    for path in (upload.data_path, upload.info_path)
                    if path is not None
                ]
                last_activity = get_last_activity(paths)
                # the upload was resumed while this run was deciding about it
                if last_activity is not None and now - last_activity < upload.retention:
                    stats["items_skipped"] += 1
                    continue
                if not remove_upload_from_tusd(
                    upload.data_path or upload_dir / upload.upload_id,
                    str(upload.info_path) if upload.info_path else None,
                ):
                    stats["failures"] += 1
                    continue
            logger.info(
                "%s %s tusd upload %s (%s bytes, last updated %s)",
                "Would remove" if check_only else "Removed",
                upload.kind,
                upload.upload_id,
                upload.size,
                upload.last_activity.isoformat(),
            )
            stats["items_removed"] += 1
            stats["space_freed_up"] += upload.size
            stats["removed_ids"].add(upload.upload_id)
        except Exception:
            logger.exception("Failed to clean up tusd upload %s", upload.upload_id)
            stats["failures"] += 1

    cleanup_upload_records(db, check_only)

    return stats


def cleanup_upload_records(db: Session, check_only: bool) -> int:
    """Remove upload records for uploads no longer held by the tusd server.

    Args:
        db (Session): Database session.
        check_only (bool): If True, count the records without removing them.

    Returns:
        int: Number of records removed, or that would have been removed.
    """
    try:
        if check_only:
            removed = crud.upload.count_stale(db, older_than=INCOMPLETE_RETENTION)
        else:
            removed = crud.upload.delete_stale(db, older_than=INCOMPLETE_RETENTION)
    except Exception:
        logger.exception("Failed to clean up upload records")
        return 0

    logger.info(
        "%s %d upload record(s)",
        "Would remove" if check_only else "Removed",
        removed,
    )
    return removed
