from datetime import date
from typing import Dict
from uuid import UUID

from faker import Faker
from geojson_pydantic import Feature, Polygon
from sqlalchemy.orm import Session

from app import crud
from app.models.project import Project
from app.schemas.project import ProjectCreate
from app.tests.utils.user import create_user
from app.tests.utils.utils import (
    get_geojson_feature_collection,
    random_team_name,
    random_team_description,
)


faker = Faker()


def create_project(
    db: Session,
    title: str | None = None,
    description: str | None = None,
    planting_date: date | None = None,
    harvest_date: date | None = None,
    location: Feature[Polygon, Dict] | None = None,
    owner_id: UUID | None = None,
    team_id: UUID | None = None,
    no_dates: bool = False,
) -> Project:
    """Create random project with no team association."""
    if owner_id is None:
        user = create_user(db)
        owner_id = user.id
    if title is None:
        title = random_team_name()
    if description is None:
        description = random_team_description()
    if not no_dates:
        if planting_date is None:
            planting_date = random_planting_date()
        if harvest_date is None:
            harvest_date = random_harvest_date()
    if location is None:
        feature_collection = get_geojson_feature_collection("polygon")
        location = feature_collection["geojson"]["features"][0]

    project_in = ProjectCreate(
        title=title,
        description=description,
        planting_date=planting_date,
        harvest_date=harvest_date,
        location=location,
        team_id=team_id,
    )

    project = crud.project.create_with_owner(
        db,
        obj_in=project_in,
        owner_id=owner_id,
    )

    if project["response_code"] != 201:
        raise ValueError(project["message"])
    elif project["result"]:
        project_obj = crud.project.get(db, id=project["result"].id)
        if project_obj is None:
            raise ValueError("Unable to create project")
        return project_obj
    else:
        raise ValueError("Unable to create project")


def random_harvest_date() -> date:
    """Create random harvest datetime between Sep. and Oct. of current year.

    Raises:
        TypeError: If faker returns anything other than a date object

    Returns:
        date: A random date between Sept 1 and Oct 31 of current year
    """
    harvest_date = faker.date_between(
        start_date=date(date.today().year, 9, 1),
        end_date=date(date.today().year, 10, 31),
    )

    if not isinstance(harvest_date, date):
        raise TypeError(f"Expected date object but got {type(harvest_date)}")

    return harvest_date


def random_planting_date() -> date:
    """Create random planting datetime between Apr. and May of current year.

    Raises:
        TypeError: If faker returns anything other than a date object

    Returns:
        date: A random date between Apr 1 and May 31 of current year
    """
    planting_date = faker.date_between(
        start_date=date(date.today().year, 4, 1),
        end_date=date(date.today().year, 5, 31),
    )

    if not isinstance(planting_date, date):
        raise TypeError(f"Expected date object but got {type(planting_date)}")

    return planting_date
