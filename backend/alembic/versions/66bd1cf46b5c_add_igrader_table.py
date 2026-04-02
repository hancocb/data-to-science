"""add igrader table

Revision ID: 66bd1cf46b5c
Revises: a7f2c3d8e1b4
Create Date: 2026-02-04 14:32:13.405499

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '66bd1cf46b5c'
down_revision: str | None = 'a7f2c3d8e1b4'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table('igrader',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('igrader_id', sa.UUID(), nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), nullable=True),
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'uq_igrader_igrader_id_project_id',
        'igrader',
        ['igrader_id', 'project_id'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('uq_igrader_igrader_id_project_id', table_name='igrader')
    op.drop_table('igrader')
