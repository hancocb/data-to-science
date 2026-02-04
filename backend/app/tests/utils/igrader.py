from typing import Optional

from pydantic import UUID4
from sqlalchemy.orm import Session

from app import crud
from app.schemas.igrader import IGraderPost
from app.tests.utils.project import create_project


EXAMPLE_DATA = {
    "id": "c1234567-89a0-1234-5678-901234567890",
    "calculationMode": "Tree",
    "mode": "standard",
    "species": "Oak",
    "grade": "A",
    "date_created": 1704067200.0,
    "date_modified": 1704067200.0,
    "dbh": 12.5,
    "treeHeight": 45.0,
    "formClass": 78.0,
    "crook": 0.5,
    "crookAngle": 15.0,
    "crookRatio": 0.1,
    "sweep": 0.3,
    "sweepAngle": 10.0,
    "buttOnly": False,
    "latitude": 40.4237,
    "longitude": -86.9212,
    "doyle_val": 150.0,
    "doyle_price": 200.0,
    "international_val": 175.0,
    "international_price": 225.0,
    "scribner_val": 160.0,
    "scribner_price": 210.0,
}


def create_igrader(
    db: Session,
    project_id: Optional[UUID4] = None,
    data: Optional[dict] = None,
):
    """Create an iGrader record for testing."""
    if not project_id:
        project = create_project(db)
        project_id = project.id

    post_data = data if data is not None else EXAMPLE_DATA
    igrader_post = IGraderPost(**post_data)
    igrader = crud.igrader.create_from_post(
        db, post_data=igrader_post, project_id=project_id
    )
    return igrader