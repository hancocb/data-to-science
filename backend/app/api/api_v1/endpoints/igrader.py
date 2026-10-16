import os
import shutil
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Security, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.models.enums.api_key_scope import APIKeyScope

router = APIRouter()

IGRADER_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif"}


@router.post("", response_model=schemas.IGrader)
def create_or_update_igrader(
    igrader_in: schemas.IGraderPost,
    # the mobile app's api key may only create records; the scope is pinned here so
    # it does not depend on the http method default in deps.METHOD_SCOPES
    project: models.Project = Security(
        deps.can_read_write_project_with_jwt_or_api_key,
        scopes=[APIKeyScope.CREATE.value],
    ),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create or update an iGrader record for a project.

    The payload must include an "id" field (UUID). If a record with that
    id already exists for the project, it is updated. Otherwise, a new
    record is created. The app re-sends the same id when a submission is
    edited, so the update path stays open to a key with the create scope;
    ids are client generated UUIDs and the key cannot list them.
    """
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
    # the mobile app's api key may only create records; the scope is pinned here so
    # it does not depend on the http method default in deps.METHOD_SCOPES
    project: models.Project = Security(
        deps.can_read_write_project_with_jwt_or_api_key,
        scopes=[APIKeyScope.CREATE.value],
    ),
) -> Any:
    """Upload one or more iGrader images for a project.

    Accepts JPG, PNG, or TIFF files. Original filenames are preserved
    (they should contain the image UUID). Images are stored at
    /static/projects/{project_id}/igrader_uploads/{filename} and can be
    retrieved by constructing that URL from the UUID found in iGrader
    record data. Existing files are never overwritten; an edited image
    arrives from the app under a new id.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required.",
        )

    if os.environ.get("RUNNING_TESTS") == "1":
        static_dir = Path(settings.TEST_STATIC_DIR)
    else:
        static_dir = Path(settings.STATIC_DIR)

    upload_dir = static_dir / "projects" / str(project.id) / "igrader_uploads"

    # Validate all files before writing any
    validated: List[tuple[UploadFile, str]] = []
    seen_filenames: set[str] = set()
    for file in files:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required for all files.",
            )
        filename = Path(file.filename).name
        extension = Path(filename).suffix.lower()
        if extension not in IGRADER_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file type '{file.filename}'. "
                    f"Allowed: {', '.join(sorted(IGRADER_IMAGE_EXTENSIONS))}"
                ),
            )
        if filename in seen_filenames or (upload_dir / filename).exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File '{filename}' already exists.",
            )
        seen_filenames.add(filename)
        validated.append((file, filename))

    os.makedirs(upload_dir, exist_ok=True)

    urls = []
    for file, filename in validated:
        destination = upload_dir / filename
        with open(destination, "wb") as f:
            shutil.copyfileobj(file.file, f)
        urls.append(f"/static/projects/{project.id}/igrader_uploads/{filename}")

    return {"status": "success", "urls": urls}


@router.get("", response_model=List[schemas.IGrader])
def read_multi_igrader(
    project: models.Project = Depends(deps.can_read_project),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Return all iGrader records for a project.

    Used by the web app with a signed in session; API keys are not accepted.
    """
    igraders = crud.igrader.get_multi_igrader_by_project_id(db, project_id=project.id)
    return igraders
