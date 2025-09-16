from sqlalchemy.orm import Session

from app import crud
from app.schemas.annotation import AnnotationUpdate
from app.schemas.annotation_tag import AnnotationTagCreate
from app.tests.utils.annotation import (
    create_annotation,
    create_annotation_in,
    create_multiple_annotations,
)
from app.tests.utils.data_product import SampleDataProduct
from app.tests.utils.tag import create_tag
from app.tests.utils.user import create_user


def test_create_annotation(db: Session) -> None:
    # Create a data product to associate with the annotation
    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation using utility
    annotation = create_annotation(
        db=db,
        description="Test annotation for point geometry",
        geometry_type="Point",
        data_product_id=data_product.id,
    )

    # Attach a tag to the annotation
    tag = create_tag(db)
    annotation_tag_in = AnnotationTagCreate(tag_id=tag.id)
    annotation_tag = crud.annotation_tag.create_with_annotation(
        db=db, obj_in=annotation_tag_in, annotation_id=annotation.id
    )

    # Assertions
    assert annotation.description == "Test annotation for point geometry"
    assert annotation.data_product_id == data_product.id
    assert annotation.id is not None
    assert annotation.created_at is not None
    assert annotation.updated_at is not None
    assert annotation.geom is not None  # Geometry should be stored
    assert annotation.created_by_id is None  # No user specified
    assert annotation_tag.annotation_id == annotation.id
    assert annotation_tag.tag_id == tag.id


def test_create_annotation_with_user(db: Session) -> None:
    # Create a user and data product
    user = create_user(db)
    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation with user
    annotation = create_annotation(
        db=db,
        description="Test annotation with user",
        geometry_type="Point",
        data_product_id=data_product.id,
        created_by_id=user.id,
    )

    # Assertions
    assert annotation.description == "Test annotation with user"
    assert annotation.data_product_id == data_product.id
    assert annotation.created_by_id == user.id

    # Get annotation with created_by relationship loaded
    annotation_with_user = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_user is not None
    assert annotation_with_user.created_by is not None
    assert annotation_with_user.created_by.id == user.id
    assert annotation_with_user.created_by.email == user.email


def test_get_multi_by_data_product_id(db: Session) -> None:
    # Create a data product to associate with annotations
    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create multiple annotations for the same data product
    created_annotations = create_multiple_annotations(
        db=db,
        count=2,
        data_product_id=data_product.id,
        base_description="Test annotation",
    )

    # Test get_multi_by_data_product_id
    annotations = crud.annotation.get_multi_by_data_product_id(
        db=db, data_product_id=data_product.id
    )

    # Assertions
    assert len(annotations) == 2
    annotation_ids = [annotation.id for annotation in annotations]
    created_ids = [annotation.id for annotation in created_annotations]
    for created_id in created_ids:
        assert created_id in annotation_ids


def test_update_annotation(db: Session) -> None:
    # Create annotation using utility
    annotation = create_annotation(
        db=db, description="Original description", geometry_type="Point"
    )

    # Create update data
    update_data = AnnotationUpdate(description="Updated description")

    # Update annotation
    updated_annotation = crud.annotation.update(
        db=db, db_obj=annotation, obj_in=update_data
    )

    # Assertions
    assert updated_annotation.id == annotation.id
    assert updated_annotation.description == "Updated description"
    assert updated_annotation.data_product_id == annotation.data_product_id


def test_update_annotation_with_geometry(db: Session) -> None:
    # Create annotation using utility
    annotation = create_annotation(
        db=db, description="Test annotation", geometry_type="Point"
    )

    # Create new geometry for update
    new_annotation_in = create_annotation_in(
        description="Updated with new geometry", geometry_type="LineString"
    )

    # Create update data with new geometry
    update_data = AnnotationUpdate(
        description=new_annotation_in.description, geom=new_annotation_in.geom
    )

    # Update annotation
    updated_annotation = crud.annotation.update(
        db=db, db_obj=annotation, obj_in=update_data
    )

    # Assertions
    assert updated_annotation.id == annotation.id
    assert updated_annotation.description == "Updated with new geometry"
    assert updated_annotation.geom is not None  # Geometry should be updated


def test_delete_annotation(db: Session) -> None:
    # Create annotation using utility
    annotation = create_annotation(
        db=db, description="Test annotation to delete", geometry_type="Point"
    )
    annotation_id = annotation.id

    # Delete annotation
    deleted_annotation = crud.annotation.remove(db=db, id=annotation_id)

    # Assertions
    assert deleted_annotation is not None
    assert deleted_annotation.id == annotation_id

    # Verify annotation is deleted
    retrieved_annotation = crud.annotation.get(db=db, id=annotation_id)
    assert retrieved_annotation is None


def test_annotation_created_by_id_set_to_null_when_user_deleted(db: Session) -> None:
    # Create a user and data product
    user = create_user(db)
    sample_data_product = SampleDataProduct(db)
    data_product = sample_data_product.obj

    # Create annotation with user
    annotation = create_annotation(
        db=db,
        description="Test annotation with user",
        geometry_type="Point",
        data_product_id=data_product.id,
        created_by_id=user.id,
    )

    # Verify annotation has user
    assert annotation.created_by_id == user.id

    # Get annotation with created_by relationship loaded to verify user exists
    annotation_with_user = crud.annotation.get_with_created_by(db=db, id=annotation.id)
    assert annotation_with_user is not None
    assert annotation_with_user.created_by is not None
    assert annotation_with_user.created_by.id == user.id

    # Delete the user
    crud.user.remove(db=db, id=user.id)

    # Refresh annotation from database
    updated_annotation = crud.annotation.get(db=db, id=annotation.id)

    # Assertions - annotation should still exist but created_by_id should be NULL
    assert updated_annotation is not None
    assert updated_annotation.created_by_id is None
    assert updated_annotation.description == "Test annotation with user"

    # Verify created_by relationship is None after user deletion
    updated_annotation_with_user = crud.annotation.get_with_created_by(
        db=db, id=annotation.id
    )
    assert updated_annotation_with_user is not None
    assert updated_annotation_with_user.created_by is None
