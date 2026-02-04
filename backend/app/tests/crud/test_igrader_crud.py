from typing import Sequence

from sqlalchemy.orm import Session

from app import crud
from app.tests.utils.igrader import create_igrader, EXAMPLE_DATA
from app.tests.utils.project import create_project


def test_create_igrader_record(db: Session) -> None:
    """Verify new iGrader record is created in database."""
    igrader = create_igrader(db)
    assert igrader
    assert igrader.id is not None
    assert igrader.data is not None
    assert igrader.data.get("species") == EXAMPLE_DATA.get("species")
    assert igrader.data.get("calculationMode") == EXAMPLE_DATA.get("calculationMode")
    assert igrader.data.get("dbh") == EXAMPLE_DATA.get("dbh")
    assert igrader.created_at is not None


def test_create_igrader_with_custom_data(db: Session) -> None:
    """Verify iGrader record accepts arbitrary JSON data."""
    custom_data = {
        "custom_field": "custom_value",
        "nested": {"key": "value"},
        "array": [1, 2, 3],
    }
    igrader = create_igrader(db, data=custom_data)
    assert igrader
    assert igrader.data.get("custom_field") == "custom_value"
    assert igrader.data.get("nested") == {"key": "value"}
    assert igrader.data.get("array") == [1, 2, 3]


def test_read_igrader_record(db: Session) -> None:
    """Verify iGrader record can be retrieved by id."""
    igrader = create_igrader(db)
    igrader_in_db = crud.igrader.get_igrader_by_id(
        db, igrader_id=igrader.id, project_id=igrader.project_id
    )
    assert igrader_in_db
    assert igrader_in_db.id == igrader.id
    assert igrader_in_db.data.get("species") == EXAMPLE_DATA.get("species")
    assert igrader_in_db.project_id == igrader.project_id


def test_read_igrader_record_wrong_project(db: Session) -> None:
    """Verify iGrader record is not returned for wrong project_id."""
    igrader = create_igrader(db)
    other_project = create_project(db)
    igrader_in_db = crud.igrader.get_igrader_by_id(
        db, igrader_id=igrader.id, project_id=other_project.id
    )
    assert igrader_in_db is None


def test_read_igrader_records(db: Session) -> None:
    """Verify multiple iGrader records can be retrieved by project_id."""
    project = create_project(db)
    igrader1 = create_igrader(db, project_id=project.id)
    igrader2 = create_igrader(db, project_id=project.id)
    igrader3 = create_igrader(db, project_id=project.id)
    igraders_in_db = crud.igrader.get_multi_igrader_by_project_id(
        db, project_id=project.id
    )
    assert isinstance(igraders_in_db, Sequence)
    assert len(igraders_in_db) == 3
    igrader_ids = [ig.id for ig in igraders_in_db]
    assert igrader1.id in igrader_ids
    assert igrader2.id in igrader_ids
    assert igrader3.id in igrader_ids


def test_read_igrader_records_empty(db: Session) -> None:
    """Verify empty list is returned when no iGrader records exist for project."""
    project = create_project(db)
    igraders_in_db = crud.igrader.get_multi_igrader_by_project_id(
        db, project_id=project.id
    )
    assert isinstance(igraders_in_db, Sequence)
    assert len(igraders_in_db) == 0


def test_delete_igrader_record(db: Session) -> None:
    """Verify iGrader record can be deleted."""
    igrader = create_igrader(db)
    igrader_removed = crud.igrader.remove_igrader_by_id(
        db, igrader_id=igrader.id, project_id=igrader.project_id
    )
    igrader_in_db = crud.igrader.get_igrader_by_id(
        db, igrader_id=igrader.id, project_id=igrader.project_id
    )
    assert igrader_removed  # remove method returns removed object
    assert igrader_in_db is None  # subsequent select queries return None


def test_delete_igrader_record_wrong_project(db: Session) -> None:
    """Verify iGrader record is not deleted with wrong project_id."""
    igrader = create_igrader(db)
    other_project = create_project(db)
    igrader_removed = crud.igrader.remove_igrader_by_id(
        db, igrader_id=igrader.id, project_id=other_project.id
    )
    igrader_in_db = crud.igrader.get_igrader_by_id(
        db, igrader_id=igrader.id, project_id=igrader.project_id
    )
    assert igrader_removed is None  # remove returns None when not found
    assert igrader_in_db is not None  # record still exists