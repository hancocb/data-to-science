import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .flight import Flight
    from .project import Project

DATASET_CATEGORIES = ["Field", "Ground", "UAS"]


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category: Mapped[enumerate] = mapped_column(
        ENUM(*DATASET_CATEGORIES, name="dataset_type"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="datasets")
    flight: Mapped["Flight"] = relationship(back_populates="dataset")

    def __repr__(self) -> str:
        return (
            f"Dataset(id={self.id!r}, category={self.category!r}, "
            f"project_id={self.project_id!r})"
        )