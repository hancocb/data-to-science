import os
import shutil
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()

IGRADER_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif"}


@router.post("", response_model=schemas.IGrader)
def create_or_update_igrader(
    igrader_in: schemas.IGraderPost,
    project: models.Project = Depends(deps.can_read_write_project_with_jwt_or_api_key),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create or update an iGrader record for a project.

    The payload must include an "id" field (UUID). If a record with that
    id already exists for the project, it is updated. Otherwise, a new
    record is created.
    """
    payload = igrader_in.model_dump()
    if "id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payload must include an 'id' field.",
        )
    igrader, created = crud.igrader.create_or_update_from_post(
        db, post_data=igrader_in, project_id=project.id
    )
    response_data = schemas.IGrader.model_validate(igrader).model_dump(mode="json")
    if created:
        return JSONResponse(content=response_data, status_code=status.HTTP_201_CREATED)
    return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_igrader_images(
    files: List[UploadFile],
    project: models.Project = Depends(deps.can_read_write_project_with_jwt_or_api_key),
) -> Any:
    """Upload one or more iGrader images for a project.

    Accepts JPG, PNG, or TIFF files. Original filenames are preserved
    (they should contain the image UUID). Images are stored at
    /static/projects/{project_id}/igrader_uploads/{filename} and can be
    retrieved by constructing that URL from the UUID found in iGrader
    record data.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required.",
        )

    # Validate all files before writing any
    for file in files:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required for all files.",
            )
        extension = Path(file.filename).suffix.lower()
        if extension not in IGRADER_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file type '{file.filename}'. "
                    f"Allowed: {', '.join(sorted(IGRADER_IMAGE_EXTENSIONS))}"
                ),
            )

    if os.environ.get("RUNNING_TESTS") == "1":
        static_dir = Path(settings.TEST_STATIC_DIR)
    else:
        static_dir = Path(settings.STATIC_DIR)

    upload_dir = static_dir / "projects" / str(project.id) / "igrader_uploads"
    os.makedirs(upload_dir, exist_ok=True)

    urls = []
    for file in files:
        filename = Path(file.filename).name
        destination = upload_dir / filename
        with open(destination, "wb") as f:
            shutil.copyfileobj(file.file, f)
        urls.append(
            f"/static/projects/{project.id}/igrader_uploads/{filename}"
        )

    return {"status": "success", "urls": urls}


@router.get("", response_model=List[schemas.IGrader])
def read_multi_igrader(
    project: models.Project = Depends(deps.can_read_project_with_jwt_or_api_key),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Return all iGrader records for a project."""
    igraders = crud.igrader.get_multi_igrader_by_project_id(
        db, project_id=project.id
    )
    return igraders