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
from app.tests.utils.igrader import EXAMPLE_DATA, create_igrader
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
    assert response_data["data"]["calculationMode"] == EXAMPLE_DATA.get(
        "calculationMode"
    )
    assert response_data["data"]["dbh"] == EXAMPLE_DATA.get("dbh")
    assert response_data["project_id"] == str(project.id)
    assert response_data["created_at"] is not None
    assert response_data["igrader_id"] == EXAMPLE_DATA["id"]


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
def test_create_igrader_record_with_extra_fields(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating iGrader record with extra fields beyond the standard set."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    payload = {
        "id": "a1234567-89a0-1234-5678-901234567890",
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
    assert response_data["igrader_id"] == "a1234567-89a0-1234-5678-901234567890"


@pytest_requires_igrader
def test_create_igrader_record_without_id_returns_422(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that POST without an 'id' field is rejected."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    payload = {"species": "Oak", "dbh": 12.5}
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest_requires_igrader
def test_create_igrader_record_with_empty_json_returns_422(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that POST with empty JSON object is rejected."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    payload = {}
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest_requires_igrader
def test_upsert_updates_existing_record_with_same_igrader_id(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that POST with matching data.id updates existing record."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    payload = EXAMPLE_DATA.copy()

    # First POST - creates
    response1 = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response1.status_code == status.HTTP_201_CREATED
    data1 = response1.json()
    db_id = data1["id"]

    # Second POST with same data.id but modified fields - updates
    payload["species"] = "Maple"
    payload["dbh"] = 10.0
    response2 = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response2.status_code == status.HTTP_200_OK
    data2 = response2.json()

    # Same DB record (same id), updated data
    assert data2["id"] == db_id
    assert data2["data"]["species"] == "Maple"
    assert data2["data"]["dbh"] == 10.0
    assert data2["igrader_id"] == EXAMPLE_DATA["id"]


@pytest_requires_igrader
def test_upsert_creates_separate_records_for_different_igrader_ids(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that POST with different data.id values creates separate records."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)

    payload1 = EXAMPLE_DATA.copy()
    response1 = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload1
    )
    assert response1.status_code == status.HTTP_201_CREATED

    payload2 = EXAMPLE_DATA.copy()
    payload2["id"] = "d2345678-90b1-2345-6789-012345678901"
    payload2["species"] = "Maple"
    response2 = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload2
    )
    assert response2.status_code == status.HTTP_201_CREATED

    # Should be two distinct records
    assert response1.json()["id"] != response2.json()["id"]

    # Verify via GET
    response_all = client.get(f"{settings.API_V1_STR}/projects/{project.id}/igrader")
    assert len(response_all.json()) == 2


@pytest_requires_igrader
def test_upsert_updates_updated_at_timestamp(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that updated_at changes after an update."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    payload = EXAMPLE_DATA.copy()

    # Create
    response1 = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response1.status_code == status.HTTP_201_CREATED
    data1 = response1.json()

    # Update
    payload["species"] = "Birch"
    response2 = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response2.status_code == status.HTTP_200_OK
    data2 = response2.json()

    assert data2["updated_at"] is not None
    assert data2["created_at"] == data1["created_at"]


@pytest_requires_igrader
def test_read_igrader_records_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test reading all iGrader records as project owner."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    # Create two records for the project
    create_igrader(db, project_id=project.id)
    create_igrader(
        db,
        project_id=project.id,
        data={
            "id": "d2345678-90b1-2345-6789-012345678901",
            "species": "Maple",
            "dbh": 8.0,
        },
    )
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/igrader")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 2
    for record in response_data:
        assert record["id"] is not None
        assert record["data"] is not None
        assert record["project_id"] == str(project.id)
        assert record["created_at"] is not None


@pytest_requires_igrader
def test_read_igrader_records_with_project_owner_role_and_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    """Test reading all iGrader records as project owner using API key."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, api_key=normal_user_api_key
    )
    project = create_project(db, owner_id=current_user.id)
    create_igrader(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader",
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1


@pytest_requires_igrader
def test_read_igrader_records_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test reading all iGrader records as project manager."""
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
    )
    create_igrader(db, project_id=project.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/igrader")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1


@pytest_requires_igrader
def test_read_igrader_records_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test reading all iGrader records as project viewer."""
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )
    create_igrader(db, project_id=project.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/igrader")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1


@pytest_requires_igrader
def test_read_igrader_records_without_project_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test reading iGrader records without any project role (should fail)."""
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_igrader(db, project_id=project.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/igrader")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest_requires_igrader
def test_read_igrader_records_returns_empty_list(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test reading iGrader records when none exist returns empty list."""
    current_user = get_current_approved_user_by_jwt_or_api_key(
        db, token=normal_user_access_token
    )
    project = create_project(db, owner_id=current_user.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/igrader")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 0
