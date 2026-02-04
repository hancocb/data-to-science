from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_current_approved_user_by_jwt_or_api_key,
)
from app.core.config import settings
from app.tests.conftest import pytest_requires_igrader
from app.schemas.role import Role
from app.tests.utils.igrader import EXAMPLE_DATA
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


@pytest_requires_igrader
def test_create_igrader_record_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating iGrader record as project owner."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    payload = EXAMPLE_DATA.copy()
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data
    assert response_data["id"] is not None
    assert response_data["data"] is not None
    assert response_data["data"]["species"] == EXAMPLE_DATA.get("species")
    assert response_data["data"]["calculationMode"] == EXAMPLE_DATA.get("calculationMode")
    assert response_data["data"]["dbh"] == EXAMPLE_DATA.get("dbh")
    assert response_data["project_id"] == str(project.id)
    assert response_data["created_at"] is not None


@pytest_requires_igrader
def test_create_igrader_record_with_project_owner_role_and_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    """Test creating iGrader record as project owner using API key."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, api_key=normal_user_api_key
    )
    project = create_project(db, owner_id=current_user.id)
    payload = EXAMPLE_DATA.copy()
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader",
        json=payload,
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data
    assert response_data["id"] is not None
    assert response_data["data"] is not None


@pytest_requires_igrader
def test_create_igrader_record_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating iGrader record as project manager."""
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
    )
    payload = EXAMPLE_DATA.copy()
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data
    assert response_data["id"] is not None


@pytest_requires_igrader
def test_create_igrader_record_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating iGrader record as project viewer (should fail)."""
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )
    payload = EXAMPLE_DATA.copy()
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest_requires_igrader
def test_create_igrader_record_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating iGrader record without any project role (should fail)."""
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    payload = EXAMPLE_DATA.copy()
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_igrader
def test_create_igrader_record_with_arbitrary_json(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating iGrader record with arbitrary JSON data."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    # Send arbitrary JSON - the endpoint should accept anything
    payload = {
        "custom_field": "custom_value",
        "nested": {"key": "value", "number": 42},
        "array": [1, 2, 3],
        "boolean": True,
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data
    assert response_data["data"]["custom_field"] == "custom_value"
    assert response_data["data"]["nested"] == {"key": "value", "number": 42}
    assert response_data["data"]["array"] == [1, 2, 3]
    assert response_data["data"]["boolean"] is True


@pytest_requires_igrader
def test_create_igrader_record_with_empty_json(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating iGrader record with empty JSON object."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    payload = {}
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data
    assert response_data["data"] == {}