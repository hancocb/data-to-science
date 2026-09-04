"""Helpers for removing uploads from tusd storage.

tusd writes two files per upload, "<id>" for the uploaded bytes and "<id>.info"
for the metadata it needs to resume, and never removes either one itself.
"""

import functools
import inspect
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, TypeVar

from app.core.config import settings

logger = logging.getLogger(__name__)

# tusd names uploads with 16 random bytes, hex encoded
TUSD_UPLOAD_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")

TUSD_INFO_SUFFIX = ".info"


def get_tusd_upload_dir() -> Path:
    """Get directory tusd writes uploads to.

    Returns:
        Path: Upload directory.
    """
    if os.environ.get("RUNNING_TESTS") == "1":
        return Path(settings.TEST_TUSD_UPLOAD_DIR)
    return Path(settings.TUSD_UPLOAD_DIR)


def get_info_path(
    storage_path: str | os.PathLike[str], info_path: str | None = None
) -> Path:
    """Get path for an upload's .info file.

    Args:
        storage_path (str | os.PathLike[str]): Location of upload on tusd server.
        info_path (str | None): Path reported by tusd, if the hook included one.

    Returns:
        Path: Path reported by tusd, or "<storage_path>.info".
    """
    if info_path:
        return Path(info_path)
    return Path(f"{storage_path}{TUSD_INFO_SUFFIX}")


def remove_upload_from_tusd(
    storage_path: str | os.PathLike[str], info_path: str | None = None
) -> bool:
    """Remove an upload and its .info file from tusd storage.

    Never raises, so it is safe to call from a path that is already handling a
    failure. Only the two named files are removed; a directory or symlink at
    either path is left alone and reported.

    Args:
        storage_path (str | os.PathLike[str]): Location of upload on tusd server.
        info_path (str | None): Path reported by tusd, if the hook included one.

    Returns:
        bool: False if a file that exists could not be removed, otherwise True.
    """
    removed_all = True
    for path in (Path(storage_path), get_info_path(storage_path, info_path)):
        try:
            if path.is_symlink() or path.is_dir():
                logger.warning("Refusing to remove non-file upload path %s", path)
                removed_all = False
                continue
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Unable to remove upload file %s", path)
            removed_all = False
    return removed_all


F = TypeVar("F", bound=Callable[..., Any])


def removes_tusd_upload(func: F) -> F:
    """Remove the task's upload from tusd storage on every exit.

    tusd only calls post-finish once the upload is complete, so the file is
    never resumable by the time a task receives it and can always be removed,
    whether the task succeeded, returned early, or raised.

    Args:
        func (F): Task function with a "storage_path" argument.

    Returns:
        F: Wrapped task function.
    """
    signature = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        bound_arguments = signature.bind_partial(*args, **kwargs)
        storage_path = bound_arguments.arguments.get("storage_path")
        try:
            return func(*args, **kwargs)
        finally:
            if storage_path:
                remove_upload_from_tusd(storage_path)

    return wrapper  # type: ignore[return-value]
