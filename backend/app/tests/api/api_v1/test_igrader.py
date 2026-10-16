import io
from pathlib import Path
from typing import List
from uuid import UUID

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.enums.api_key_scope import APIKeyScope
from app.schemas.role import Role
from app.tests.conftest import pytest_requires_igrader
from app.tests.utils.igrader import EXAMPLE_DATA, create_igrader
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user

JPG_BYTES = b"\xff\xd8\xff\xe0fake-jpg-data"


def scope_error(scope: APIKeyScope) -> str:
    return f"API key does not have the '{scope.value}' scope"


def create_user_api_key(db: Session, scopes: List[APIKeyScope]) -> tuple:
    user = create_user(db)
    api_key = crud.api_key.create_with_user(db, user_id=user.id, scopes=scopes)
    return user, api_key.api_key


def igrader_upload_dir(project_id: UUID) -> Path:
    return (
        Path(settings.TEST_STATIC_DIR)
        / "projects"
        / str(project_id)
        / "igrader_uploads"
    )


def jpg_upload(filename: str, content: bytes = JPG_BYTES) -> tuple:
    return ("files", (filename, io.BytesIO(content), "image/jpeg"))


@pytest_requires_igrader
def test_create_igrader_record_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating iGrader record as project owner."""
    current_user = get_current_user(db, normal_user_access_token)
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
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user
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
    current_user = get_current_user(db, normal_user_access_token)
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
    current_user = get_current_user(db, normal_user_access_token)
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
    current_user = get_current_user(db, normal_user_access_token)
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
    current_user = get_current_user(db, normal_user_access_token)
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
    current_user = get_current_user(db, normal_user_access_token)
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
    current_user = get_current_user(db, normal_user_access_token)
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
    current_user = get_current_user(db, normal_user_access_token)
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
def test_read_igrader_records_rejects_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    # key has every scope and its owner owns the project; the auth method is rejected
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user
    project = create_project(db, owner_id=current_user.id)
    create_igrader(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader",
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest_requires_igrader
def test_read_igrader_records_rejects_create_only_api_key(
    client: TestClient, db: Session
) -> None:
    # a leaked mobile app key cannot be used to read the records it created
    user, api_key = create_user_api_key(db, [APIKeyScope.CREATE])
    project = create_project(db, owner_id=user.id)
    create_igrader(db, project_id=project.id)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


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
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    response = client.get(f"{settings.API_V1_STR}/projects/{project.id}/igrader")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 0


# --- Upload endpoint tests ---


@pytest_requires_igrader
def test_upload_igrader_image_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test uploading an iGrader image as project owner."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    file_content = b"\xff\xd8\xff\xe0fake-jpg-data"
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[
            (
                "files",
                (
                    "a1234567-89a0-1234-5678-901234567890.jpg",
                    io.BytesIO(file_content),
                    "image/jpeg",
                ),
            )
        ],
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "success"
    assert len(data["urls"]) == 1
    assert "igrader_uploads" in data["urls"][0]
    assert "a1234567-89a0-1234-5678-901234567890.jpg" in data["urls"][0]


@pytest_requires_igrader
def test_upload_igrader_image_with_api_key(
    client: TestClient, db: Session, normal_user_api_key: str
) -> None:
    """Test uploading an iGrader image using API key."""
    current_user = crud.user.get_by_api_key(db, api_key=normal_user_api_key)
    assert current_user
    project = create_project(db, owner_id=current_user.id)
    file_content = b"\xff\xd8\xff\xe0fake-jpg-data"
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[("files", ("test-image.jpg", io.BytesIO(file_content), "image/jpeg"))],
        headers={"X-API-KEY": normal_user_api_key},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "success"


@pytest_requires_igrader
def test_upload_igrader_image_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test uploading an iGrader image as project manager."""
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role=Role.MANAGER, member_id=current_user.id, project_uuid=project.id
    )
    file_content = b"\xff\xd8\xff\xe0fake-jpg-data"
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[("files", ("test-image.jpg", io.BytesIO(file_content), "image/jpeg"))],
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest_requires_igrader
def test_upload_igrader_image_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test uploading an iGrader image as project viewer (should fail)."""
    current_user = get_current_user(db, normal_user_access_token)
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    create_project_member(
        db, role=Role.VIEWER, member_id=current_user.id, project_uuid=project.id
    )
    file_content = b"\xff\xd8\xff\xe0fake-jpg-data"
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[("files", ("test-image.jpg", io.BytesIO(file_content), "image/jpeg"))],
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest_requires_igrader
def test_upload_igrader_image_unsupported_extension(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test uploading an iGrader image with unsupported extension."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    file_content = b"fake-gif-data"
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[("files", ("test-image.gif", io.BytesIO(file_content), "image/gif"))],
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported file type" in response.json()["detail"]


@pytest_requires_igrader
def test_upload_igrader_image_png(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test uploading a PNG iGrader image."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    file_content = b"\x89PNG\r\n\x1a\nfake-png-data"
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[("files", ("test-image.png", io.BytesIO(file_content), "image/png"))],
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "success"
    assert "test-image.png" in data["urls"][0]


@pytest_requires_igrader
def test_upload_igrader_image_tif(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test uploading a TIFF iGrader image."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    file_content = b"II*\x00fake-tif-data"
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[("files", ("test-image.tif", io.BytesIO(file_content), "image/tiff"))],
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "success"
    assert "test-image.tif" in data["urls"][0]


@pytest_requires_igrader
def test_upload_multiple_igrader_images(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test uploading multiple iGrader images at once."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[
            (
                "files",
                ("image-1.jpg", io.BytesIO(b"\xff\xd8\xff\xe0data1"), "image/jpeg"),
            ),
            ("files", ("image-2.png", io.BytesIO(b"\x89PNGdata2"), "image/png")),
            ("files", ("image-3.tif", io.BytesIO(b"II*\x00data3"), "image/tiff")),
        ],
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "success"
    assert len(data["urls"]) == 3
    assert "image-1.jpg" in data["urls"][0]
    assert "image-2.png" in data["urls"][1]
    assert "image-3.tif" in data["urls"][2]


@pytest_requires_igrader
def test_upload_multiple_igrader_images_one_invalid(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test that one invalid file in a batch rejects the entire upload."""
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[
            ("files", ("valid.jpg", io.BytesIO(b"\xff\xd8\xff\xe0data"), "image/jpeg")),
            ("files", ("invalid.gif", io.BytesIO(b"gifdata"), "image/gif")),
        ],
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid.gif" in response.json()["detail"]


# --- API key scope tests ---


@pytest_requires_igrader
def test_create_igrader_record_with_create_only_api_key(
    client: TestClient, db: Session
) -> None:
    # a key embedded in a mobile app can add records but cannot read project data
    user, api_key = create_user_api_key(db, [APIKeyScope.CREATE])
    project = create_project(db, owner_id=user.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader",
        json=EXAMPLE_DATA.copy(),
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert len(crud.igrader.get_multi_igrader_by_project_id(db, project.id)) == 1
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.id}",
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(APIKeyScope.READ)


@pytest_requires_igrader
@pytest.mark.parametrize(
    "scopes", [[APIKeyScope.READ], [APIKeyScope.UPDATE], [APIKeyScope.DELETE]]
)
def test_create_igrader_requires_create_scope(
    client: TestClient, db: Session, scopes: List[APIKeyScope]
) -> None:
    user, api_key = create_user_api_key(db, scopes)
    project = create_project(db, owner_id=user.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader",
        json=EXAMPLE_DATA.copy(),
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(APIKeyScope.CREATE)
    assert crud.igrader.get_multi_igrader_by_project_id(db, project.id) == []


@pytest_requires_igrader
def test_create_igrader_record_with_non_uuid_id_returns_422(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    current_user = get_current_user(db, normal_user_access_token)
    project = create_project(db, owner_id=current_user.id)
    payload = {**EXAMPLE_DATA, "id": "not-a-uuid"}
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader", json=payload
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert crud.igrader.get_multi_igrader_by_project_id(db, project.id) == []


@pytest_requires_igrader
def test_upsert_with_create_only_api_key_updates_existing_record(
    client: TestClient, db: Session
) -> None:
    # the app re-sends the same id when a submission is edited
    user, api_key = create_user_api_key(db, [APIKeyScope.CREATE])
    project = create_project(db, owner_id=user.id)
    url = f"{settings.API_V1_STR}/projects/{project.id}/igrader"
    headers = {"X-API-KEY": api_key}
    payload = EXAMPLE_DATA.copy()
    response1 = client.post(url, json=payload, headers=headers)
    assert response1.status_code == status.HTTP_201_CREATED
    payload["species"] = "Maple"
    response2 = client.post(url, json=payload, headers=headers)
    assert response2.status_code == status.HTTP_200_OK
    assert response2.json()["id"] == response1.json()["id"]
    assert response2.json()["data"]["species"] == "Maple"
    assert len(crud.igrader.get_multi_igrader_by_project_id(db, project.id)) == 1


@pytest_requires_igrader
def test_upload_igrader_image_with_create_only_api_key(
    client: TestClient, db: Session
) -> None:
    user, api_key = create_user_api_key(db, [APIKeyScope.CREATE])
    project = create_project(db, owner_id=user.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[jpg_upload("test-image.jpg")],
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert (igrader_upload_dir(project.id) / "test-image.jpg").read_bytes() == JPG_BYTES


@pytest_requires_igrader
@pytest.mark.parametrize(
    "scopes", [[APIKeyScope.READ], [APIKeyScope.UPDATE], [APIKeyScope.DELETE]]
)
def test_upload_igrader_image_requires_create_scope(
    client: TestClient, db: Session, scopes: List[APIKeyScope]
) -> None:
    user, api_key = create_user_api_key(db, scopes)
    project = create_project(db, owner_id=user.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[jpg_upload("test-image.jpg")],
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == scope_error(APIKeyScope.CREATE)
    assert not (igrader_upload_dir(project.id) / "test-image.jpg").exists()


@pytest_requires_igrader
def test_upload_igrader_image_refuses_overwrite(
    client: TestClient, db: Session
) -> None:
    # an edited image arrives under a new id, so an existing file is never replaced
    user, api_key = create_user_api_key(db, [APIKeyScope.CREATE])
    project = create_project(db, owner_id=user.id)
    url = f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload"
    headers = {"X-API-KEY": api_key}
    response = client.post(url, files=[jpg_upload("a.jpg")], headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    response = client.post(
        url, files=[jpg_upload("a.jpg", b"\xff\xd8\xff\xe0other")], headers=headers
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "a.jpg" in response.json()["detail"]
    assert (igrader_upload_dir(project.id) / "a.jpg").read_bytes() == JPG_BYTES


@pytest_requires_igrader
def test_upload_igrader_images_rejects_duplicate_filenames_in_request(
    client: TestClient, db: Session
) -> None:
    user, api_key = create_user_api_key(db, [APIKeyScope.CREATE])
    project = create_project(db, owner_id=user.id)
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.id}/igrader/upload",
        files=[jpg_upload("a.jpg"), jpg_upload("a.jpg", b"\xff\xd8\xff\xe0other")],
        headers={"X-API-KEY": api_key},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert not igrader_upload_dir(project.id).exists()
