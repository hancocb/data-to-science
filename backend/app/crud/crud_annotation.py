import json
from typing import Any, Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.crud.base import CRUDBase
from app.models.annotation import Annotation
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate


class CRUDAnnotation(CRUDBase[Annotation, AnnotationCreate, AnnotationUpdate]):
    def create_with_data_product(
        self,
        db: Session,
        *,
        obj_in: AnnotationCreate,
        data_product_id: UUID,
        created_by_id: UUID | None = None,
    ) -> Annotation:
        """Create a new annotation with proper geometry handling.

        Args:
            db (Session): Database session.
            obj_in (AnnotationCreate): Annotation data to create.
            data_product_id (UUID): ID of the data product this annotation belongs to.
            created_by_id (UUID | None): ID of the user who created this annotation.

        Returns:
            Annotation: Created annotation object.
        """
        # Convert to dict for processing
        obj_in_data = jsonable_encoder(obj_in)

        # Extract geometry from GeoJSON Feature
        feature = obj_in_data["geom"]
        geometry = feature["geometry"]

        # Convert geometry to PostGIS format
        geom = func.ST_Force2D(func.ST_GeomFromGeoJSON(json.dumps(geometry)))

        # Create annotation object with processed geometry
        db_obj = Annotation(
            description=obj_in_data["description"],
            geom=geom,
            data_product_id=data_product_id,
            created_by_id=created_by_id,
        )

        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)

        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Annotation,
        obj_in: AnnotationUpdate | dict[str, Any],
    ) -> Annotation:
        """Update an annotation with proper geometry handling.

        Args:
            db (Session): Database session.
            db_obj (Annotation): Existing annotation object.
            obj_in (AnnotationUpdate | dict): Update data.

        Returns:
            Annotation: Updated annotation object.
        """
        # Convert to dict for processing
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Handle geometry update if provided
        if "geom" in update_data and update_data["geom"] is not None:
            feature = update_data["geom"]
            # Extract geometry from GeoJSON Feature
            if isinstance(feature, dict):
                geometry = feature["geometry"]
            else:
                # Handle pydantic Feature object
                geometry = feature.geometry

            # Convert geometry to PostGIS format
            geom = func.ST_Force2D(func.ST_GeomFromGeoJSON(json.dumps(geometry)))
            db_obj.geom = geom

        # Update other simple fields (excluding geometry which we handled above)
        for field, value in update_data.items():
            if field != "geom" and hasattr(db_obj, field):
                setattr(db_obj, field, value)

        with db as session:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)

        return db_obj

    def get_multi_by_data_product_id(
        self, db: Session, data_product_id: UUID
    ) -> Sequence[Annotation]:
        """Return all annotations for a data product.

        Args:
            db (Session): Database session.
            data_product_id (UUID): Data product ID.

        Returns:
            Sequence[Annotation]: List of annotations for the data product.
        """
        statement = select(Annotation).where(
            Annotation.data_product_id == data_product_id
        )

        with db as session:
            annotations = session.scalars(statement).all()
            return annotations

    def get_with_created_by(self, db: Session, id: UUID) -> Annotation | None:
        """Get an annotation with the created_by relationship loaded.

        Args:
            db (Session): Database session.
            id (UUID): Annotation ID.

        Returns:
            Annotation | None: Annotation with created_by loaded, or None if not found.
        """
        statement = (
            select(Annotation)
            .options(selectinload(Annotation.created_by))
            .where(Annotation.id == id)
        )

        with db as session:
            return session.scalar(statement)


annotation = CRUDAnnotation(Annotation)
