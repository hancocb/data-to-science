from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.post("", response_model=schemas.IGrader, status_code=status.HTTP_201_CREATED)
def create_igrader(
    igrader_in: schemas.IGraderPost,
    project: models.Project = Depends(deps.can_read_write_project_with_jwt_or_api_key),
    db: Session = Depends(deps.get_db),
) -> Any:
    """Create a new iGrader record for a project.

    Accepts any JSON payload and stores it in the database.
    """
    igrader = crud.igrader.create_from_post(
        db, post_data=igrader_in, project_id=project.id
    )
    return igrader