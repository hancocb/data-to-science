"""add igrader table

Revision ID: 66bd1cf46b5c
Revises: 560e396bce4f
Create Date: 2026-02-04 14:32:13.405499

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '66bd1cf46b5c'
down_revision: str | None = '560e396bce4f'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table('igrader',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('igrader')
