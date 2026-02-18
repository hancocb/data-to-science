from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


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