"""Extensions allowed for files uploaded to tusd.

Checked at pre-create so tusd rejects an unsupported file before storing any
bytes, and again during post processing.
"""

from pathlib import Path

from app.api.utils import get_file_extension

DATA_PRODUCT_EXTENSIONS = {
    ".tif",
    ".las",
    ".laz",
    ".copc.laz",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".avif",
    ".ply",
    ".zip",
}

RAW_DATA_EXTENSIONS = {".zip"}

ANNOTATION_ATTACHMENT_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".mp4",
    ".mov",
    ".webm",
    ".avi",
}

INDOOR_DATA_EXTENSIONS = {".xls", ".xlsx", ".tar"}


class UnsupportedUploadExtension(ValueError):
    """Raised when an uploaded file's extension is not allowed."""


def validate_data_product_extension(filename: Path) -> str:
    """Check extension of an uploaded data product.

    Args:
        filename (Path): Original name of uploaded data product.

    Raises:
        UnsupportedUploadExtension: Raised if extension is not supported.

    Returns:
        str: Extension of the uploaded data product.
    """
    extension = get_file_extension(filename)
    if extension not in DATA_PRODUCT_EXTENSIONS:
        raise UnsupportedUploadExtension("Unsupported file extension")
    return extension


def validate_raw_data_extension(filename: Path) -> str:
    """Check extension of uploaded raw data.

    Args:
        filename (Path): Original name of uploaded raw data.

    Raises:
        UnsupportedUploadExtension: Raised if extension is not supported.

    Returns:
        str: Extension of the uploaded raw data.
    """
    extension = filename.suffix.lower()
    if extension not in RAW_DATA_EXTENSIONS:
        raise UnsupportedUploadExtension("Raw data must be in .zip")
    return extension


def validate_annotation_attachment_extension(filename: Path) -> str:
    """Check extension of an uploaded annotation attachment.

    Args:
        filename (Path): Original name of uploaded attachment.

    Raises:
        UnsupportedUploadExtension: Raised if extension is not supported.

    Returns:
        str: Extension of the uploaded attachment.
    """
    extension = filename.suffix.lower()
    if extension not in ANNOTATION_ATTACHMENT_EXTENSIONS:
        raise UnsupportedUploadExtension(
            f"Unsupported file type. Allowed: "
            f"{', '.join(sorted(ANNOTATION_ATTACHMENT_EXTENSIONS))}"
        )
    return extension


def validate_indoor_data_extension(filename: Path) -> str:
    """Check extension of uploaded indoor project data.

    Args:
        filename (Path): Original name of uploaded indoor project data.

    Raises:
        UnsupportedUploadExtension: Raised if extension is not supported.

    Returns:
        str: Extension of the uploaded indoor project data.
    """
    extension = filename.suffix.lower()
    if extension not in INDOOR_DATA_EXTENSIONS:
        raise UnsupportedUploadExtension(
            "Indoor data must be spreadsheet (.xls, .xlsx) or tar archive (.tar)"
        )
    return extension


def validate_upload_extension(
    filename: Path, data_type: str | None = None, is_indoor: bool = False
) -> str:
    """Check extension of an uploaded file against the rules for its data type.

    Args:
        filename (Path): Original name of uploaded file.
        data_type (str | None): Value of the "X-Data-Type" header.
        is_indoor (bool): True if the upload belongs to an indoor project.

    Raises:
        UnsupportedUploadExtension: Raised if extension is not supported.

    Returns:
        str: Extension of the uploaded file.
    """
    if is_indoor:
        return validate_indoor_data_extension(filename)
    if data_type == "raw":
        return validate_raw_data_extension(filename)
    if data_type == "annotation_attachment":
        return validate_annotation_attachment_extension(filename)
    return validate_data_product_extension(filename)
