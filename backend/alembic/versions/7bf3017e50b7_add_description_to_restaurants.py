"""add description to restaurants

Revision ID: 7bf3017e50b7
Revises: a5ecc734897f
Create Date: 2026-08-27 20:41:32.994261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bf3017e50b7'
down_revision: Union[str, None] = 'a5ecc734897f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('restaurants', sa.Column('description', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('restaurants', 'description')
