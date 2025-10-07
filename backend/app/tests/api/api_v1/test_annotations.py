from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.role import Role
from app.tests.utils.annotation import (
    create_annotation,
    create_annotation_in,
    create_multiple_annotations,
)
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.project_member import create_project_member
from app.tests.utils.user import create_user


def test_create_annotation_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation_in = create_annotation_in(description="Owner's annotation")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_in.model_dump(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert "id" in response_data
    assert response_data["description"] == "Owner's annotation"
    assert "geom" in response_data
    assert response_data["data_product_id"] == str(data_product.obj.id)
    assert response_data["created_by_id"] == str(current_user.id)


def test_create_annotation_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation with project manager role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role=Role.MANAGER,
    )
    annotation_in = create_annotation_in(description="Manager's annotation")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_in.model_dump(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["description"] == "Manager's annotation"
    assert response_data["created_by_id"] == str(current_user.id)


def test_create_annotation_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation with project viewer role (should fail)."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role=Role.VIEWER,
    )
    annotation_in = create_annotation_in(description="Viewer's annotation")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_in.model_dump(),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_annotation_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating an annotation without project access."""
    data_product = SampleDataProduct(db)
    annotation_in = create_annotation_in(description="Unauthorized annotation")

    response = client.post(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
        json=annotation_in.model_dump(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_annotation_with_different_geometry_types(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test creating annotations with different geometry types."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    geometry_types = ["Point", "LineString", "Polygon"]

    for geom_type in geometry_types:
        annotation_in = create_annotation_in(
            description=f"{geom_type} annotation", geometry_type=geom_type
        )

        response = client.post(
            f"{settings.API_V1_STR}/projects/{data_product.project.id}"
            f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations",
            json=annotation_in.model_dump(),
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["description"] == f"{geom_type} annotation"
        assert response_data["geom"]["geometry"]["type"] == geom_type


def test_get_annotation_by_id_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting an annotation by ID with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db, data_product_id=data_product.obj.id, created_by_id=current_user.id
    )

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)
    assert response_data["description"] == annotation.description
    assert "created_by" in response_data
    assert response_data["created_by"]["id"] == str(current_user.id)


def test_get_annotation_by_id_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting an annotation by ID with project viewer role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role=Role.VIEWER,
    )
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)


def test_get_annotation_by_id_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting an annotation by ID without project access."""
    data_product = SampleDataProduct(db)
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_annotation_by_id_not_found(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting a non-existent annotation by ID."""
    from uuid import uuid4

    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    fake_annotation_id = uuid4()

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{fake_annotation_id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_annotation_from_different_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting an annotation that belongs to a different data product."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product_1 = SampleDataProduct(db, user=current_user)
    data_product_2 = SampleDataProduct(db, user=current_user)

    # Create annotation for data_product_1
    annotation = create_annotation(db, data_product_id=data_product_1.obj.id)

    # Try to get annotation via data_product_2's URL
    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product_2.project.id}"
        f"/flights/{data_product_2.flight.id}/data_products/{data_product_2.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_annotations_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting all annotations for a data product with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotations = create_multiple_annotations(
        db, count=3, data_product_id=data_product.obj.id, created_by_id=current_user.id
    )

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 3

    annotation_ids = {str(a.id) for a in annotations}
    for annotation_data in response_data:
        assert annotation_data["id"] in annotation_ids
        assert "description" in annotation_data
        assert "geom" in annotation_data


def test_get_annotations_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting all annotations for a data product with project viewer role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role=Role.VIEWER,
    )
    create_multiple_annotations(db, count=2, data_product_id=data_product.obj.id)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 2


def test_get_annotations_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting annotations without project access."""
    data_product = SampleDataProduct(db)
    create_multiple_annotations(db, count=2, data_product_id=data_product.obj.id)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_annotations_returns_empty_list(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test getting annotations when none exist."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 0


def test_update_annotation_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db,
        description="Original description",
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
    )

    update_data = {"description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)
    assert response_data["description"] == "Updated description"


def test_update_annotation_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation with project manager role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role=Role.MANAGER,
    )
    annotation = create_annotation(
        db, description="Original", data_product_id=data_product.obj.id
    )

    update_data = {"description": "Manager updated"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["description"] == "Manager updated"


def test_update_annotation_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation with project viewer role (should fail)."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role=Role.VIEWER,
    )
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    update_data = {"description": "Viewer update attempt"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_annotation_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation without project access."""
    data_product = SampleDataProduct(db)
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    update_data = {"description": "Unauthorized update"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_annotation_geometry(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation's geometry."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db,
        geometry_type="Point",
        data_product_id=data_product.obj.id,
        created_by_id=current_user.id,
    )

    # Create new geometry
    new_annotation_in = create_annotation_in(geometry_type="Polygon")
    update_data = {"geom": new_annotation_in.geom.model_dump()}

    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)
    assert response_data["geom"]["geometry"]["type"] == "Polygon"


def test_update_annotation_not_found(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating a non-existent annotation."""
    from uuid import uuid4

    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    fake_annotation_id = uuid4()

    update_data = {"description": "Update non-existent"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{fake_annotation_id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_annotation_from_different_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test updating an annotation that belongs to a different data product."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product_1 = SampleDataProduct(db, user=current_user)
    data_product_2 = SampleDataProduct(db, user=current_user)

    # Create annotation for data_product_1
    annotation = create_annotation(db, data_product_id=data_product_1.obj.id)

    # Try to update annotation via data_product_2's URL
    update_data = {"description": "Wrong data product update"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{data_product_2.project.id}"
        f"/flights/{data_product_2.flight.id}/data_products/{data_product_2.obj.id}/annotations/{annotation.id}",
        json=update_data,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_annotation_with_project_owner_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation with project owner role."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    annotation = create_annotation(
        db, data_product_id=data_product.obj.id, created_by_id=current_user.id
    )

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(annotation.id)

    # Verify annotation is deleted
    deleted_annotation = crud.annotation.get(db, id=annotation.id)
    assert deleted_annotation is None


def test_delete_annotation_with_project_manager_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation with project manager role (should fail)."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role=Role.MANAGER,
    )
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_annotation_with_project_viewer_role(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation with project viewer role (should fail)."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db)
    create_project_member(
        db,
        member_id=current_user.id,
        project_id=data_product.project.id,
        role=Role.VIEWER,
    )
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_annotation_without_project_access(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation without project access."""
    data_product = SampleDataProduct(db)
    annotation = create_annotation(db, data_product_id=data_product.obj.id)

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_annotation_not_found(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting a non-existent annotation."""
    from uuid import uuid4

    current_user = get_current_user(db, normal_user_access_token)
    data_product = SampleDataProduct(db, user=current_user)
    fake_annotation_id = uuid4()

    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product.project.id}"
        f"/flights/{data_product.flight.id}/data_products/{data_product.obj.id}/annotations/{fake_annotation_id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_annotation_from_different_data_product(
    client: TestClient, db: Session, normal_user_access_token: str
) -> None:
    """Test deleting an annotation that belongs to a different data product."""
    current_user = get_current_user(db, normal_user_access_token)
    data_product_1 = SampleDataProduct(db, user=current_user)
    data_product_2 = SampleDataProduct(db, user=current_user)

    # Create annotation for data_product_1
    annotation = create_annotation(db, data_product_id=data_product_1.obj.id)

    # Try to delete annotation via data_product_2's URL
    response = client.delete(
        f"{settings.API_V1_STR}/projects/{data_product_2.project.id}"
        f"/flights/{data_product_2.flight.id}/data_products/{data_product_2.obj.id}/annotations/{annotation.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
