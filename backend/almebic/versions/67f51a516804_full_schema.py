"""full schema

Revision ID: 67f51a516804
Revises:
Create Date: 2026-01-17 04:43:03.529096

"""

from typing import Sequence, Union
import pgvector
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "67f51a516804"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define embedding size constant (must match utils/constants.py)
EMBEDDING_SIZE = 1024
# EMBEDDING_SIZE = 768



def upgrade() -> None:
    """Upgrade schema."""
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # 1. Create base tables first (no foreign key dependencies)
    
    # Projects table
    op.create_table(
        "projects",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("delivered", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("name"),
    )
    
    # Developers table
    op.create_table(
        "developers",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column("skills", sa.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint("name"),
    )
    
    # 2. Create tables with foreign keys to base tables
    
    # Meetings table (depends on projects)
    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["project_name"], ["projects.name"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Meeting Chunks table (depends on meetings)
    op.create_table(
        "meeting_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(dim=EMBEDDING_SIZE), nullable=True),
        sa.Column("speaker_names", sa.ARRAY(sa.String()), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Notes table (depends on projects)
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(dim=EMBEDDING_SIZE), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("tags", sa.String(length=255), nullable=True),
        sa.Column("function", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=50), nullable=True),
        sa.Column("module", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["project_name"], ["projects.name"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Tasks table (depends on projects and developers)
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("assignee_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["project_name"], ["projects.name"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignee_name"], ["developers.name"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Category Maps table (depends on projects)
    op.create_table(
        "category_maps",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["project_name"], ["projects.name"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("name", "project_name"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse dependency order
    op.drop_table("category_maps")
    op.drop_table("tasks")
    op.drop_table("notes")
    op.drop_table("meeting_chunks")
    op.drop_table("meetings")
    op.drop_table("developers")
    op.drop_table("projects")
    op.execute("DROP EXTENSION IF EXISTS vector")

