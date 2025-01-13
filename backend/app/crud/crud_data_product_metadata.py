from typing import Sequence
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import crud
from app.crud.base import CRUDBase
from app.models.data_product_metadata import DataProductMetadata
from app.models.vector_layer import VectorLayer
from app.schemas.data_product_metadata import (
    DataProductMetadataCreate,
    DataProductMetadataUpdate,
)


class CRUDDataProductMetadata(
    CRUDBase[DataProductMetadata, DataProductMetadataCreate, DataProductMetadataUpdate]
):
    def create_with_data_product(
        self, db: Session, obj_in: DataProductMetadataCreate, data_product_id: UUID
    ) -> DataProductMetadata:
        obj_in_json = jsonable_encoder(obj_in)
        metadata = DataProductMetadata(**obj_in_json, data_product_id=data_product_id)
        with db as session:
            session.add(metadata)
            session.commit()
            session.refresh(metadata)
        return metadata

    def get_by_data_product(
        self,
        db: Session,
        category: str,
        data_product_id: UUID,
        vector_layer_feature_id: UUID | None = None,
    ) -> Sequence[DataProductMetadata]:
        if vector_layer_feature_id:
            metadata_query = select(DataProductMetadata).where(
                and_(
                    DataProductMetadata.category == category,
                    DataProductMetadata.data_product_id == data_product_id,
                    DataProductMetadata.vector_layer_feature_id
                    == vector_layer_feature_id,
                )
            )
        else:
            metadata_query = select(DataProductMetadata).where(
                and_(
                    DataProductMetadata.category == category,
                    DataProductMetadata.data_product_id == data_product_id,
                )
            )
        with db as session:
            metadata = session.scalars(metadata_query).all()
            return metadata

    def get_zonal_statistics_by_layer_id(
        self, db: Session, data_product_id: UUID, layer_id: str
    ) -> Sequence[DataProductMetadata]:
        zonal_statistics_query = (
            select(DataProductMetadata)
            .join(DataProductMetadata.vector_layer)
            .where(
                and_(
                    DataProductMetadata.category == "zonal",
                    DataProductMetadata.data_product_id == data_product_id,
                    VectorLayer.layer_id == layer_id,
                )
            )
        )

        with db as session:
            metadata = session.scalars(zonal_statistics_query).all()
            return metadata


data_product_metadata = CRUDDataProductMetadata(DataProductMetadata)
