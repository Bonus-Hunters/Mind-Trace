"""add pg_trgm extension

Revision ID: 808a96fff207
Revises: 860c715415d0
Create Date: 2026-04-12 14:40:07.354249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '808a96fff207'
down_revision: Union[str, Sequence[str], None] = 'bf2f61e75eaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
