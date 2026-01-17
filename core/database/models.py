from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Optional
from sqlalchemy import String, ForeignKey, DateTime, ARRAY, Text, ForeignKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from utils.constants import EMBEDDING_SIZE


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered: Mapped[bool] = mapped_column(default=False)

    # Relationships
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    meetings: Mapped[List["Meeting"]] = relationship(
        back_populates="project_ref", cascade="all, delete-orphan"
    )
    notes: Mapped[List["Note"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class CategoryMap(Base):
    __tablename__ = "category_maps"

    name: Mapped[str] = mapped_column(primary_key=True)
    project_name: Mapped[str] = mapped_column(
        ForeignKey("projects.name"), primary_key=True
    )
    type: Mapped[str] = mapped_column(String(50))


class Developer(Base):
    __tablename__ = "developers"

    name: Mapped[str] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(100), nullable=True)
    skills: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)

    # Relationship for Tasks
    tasks: Mapped[List["Task"]] = relationship(back_populates="owner")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    date: Mapped[datetime] = mapped_column(DateTime)
    project_name: Mapped[str] = mapped_column(ForeignKey("projects.name"))

    # relations
    project_ref: Mapped["Project"] = relationship(back_populates="meetings")
    chunks: Mapped[List["MeetingChunk"]] = relationship(back_populates="meeting")


class MeetingChunk(Base):
    __tablename__ = "meeting_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE")
    )
    text_content: Mapped[str] = mapped_column(Text)

    # Using pgvector for embeddings (requires 'pip install pgvector')
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(dim=EMBEDDING_SIZE))

    # FKs to Developers (Speakers)
    speaker_names: Mapped[List[str]] = mapped_column(ARRAY(String))

    meeting: Mapped["Meeting"] = relationship(back_populates="chunks")


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(
        String(255), ForeignKey("projects.name", ondelete="CASCADE")
    )
    author: Mapped[str] = mapped_column(String(255))
    note_text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[List[float]] = mapped_column(Vector(dim=EMBEDDING_SIZE))
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    type: Mapped[str] = mapped_column(String(50))
    tags: Mapped[str] = mapped_column(String(255), nullable=True)
    function: Mapped[str] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(String(50), nullable=True)
    module: Mapped[str] = mapped_column(String(50), nullable=True)

    # relation
    project: Mapped["Project"] = relationship(
        back_populates="notes", foreign_keys=[project_name]
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(
        ForeignKey("projects.name", ondelete="CASCADE")
    )
    assignee_name: Mapped[str] = mapped_column(
        ForeignKey("developers.name", ondelete="SET NULL")
    )
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50)
    )  # e.g., 'todo', 'in_progress', 'done'

    # Polymorphic-lite reference
    source_type: Mapped[str] = mapped_column(String(20))  # 'note' or 'meeting'

    project: Mapped["Project"] = relationship(back_populates="tasks")
    owner: Mapped["Developer"] = relationship(back_populates="tasks")
