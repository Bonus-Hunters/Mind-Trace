"""merge heads

Revision ID: db_merge_heads
Revises: 81c1c9955489, 808a96fff207
Create Date: 2026-06-28 01:32:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db_merge_heads'
down_revision: Union[str, Sequence[str], None] = ('81c1c9955489', '808a96fff207')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
