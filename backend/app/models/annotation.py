import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.utils.utcnow import utcnow


if TYPE_CHECKING:
    from .annotation_attachment import AnnotationAttachment
    from .annotation_tag import AnnotationTag
    from .data_product import DataProduct


class Annotation(Base):
    __tablename__ = "annotations"

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=utcnow(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    )

    # Foreign keys
    data_product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_products.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    data_product: Mapped["DataProduct"] = relationship(
        back_populates="annotations",
        lazy="joined",
    )
    attachments: Mapped[List["AnnotationAttachment"]] = relationship(
        back_populates="annotation",
        cascade="all, delete-orphan",
    )
    tag_rows: Mapped[List["AnnotationTag"]] = relationship(
        back_populates="annotation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"Annotation(id={self.id!r}, description={self.description!r}, "
            f"created_at={self.created_at!r}, updated_at={self.updated_at!r}, "
            f"data_product_id={self.data_product_id!r})"
        )
