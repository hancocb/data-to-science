"""include original filename in raw data uploads

Revision ID: e7b52834029e
Revises: 6073062cc3fe
Create Date: 2023-08-18 18:35:29.629346

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7b52834029e'
down_revision: str | None = '6073062cc3fe'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('raw_data', sa.Column('original_filename', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('raw_data', 'original_filename')
    # ### end Alembic commands ###