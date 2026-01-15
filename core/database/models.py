from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Optional
from sqlalchemy import String, ForeignKey, DateTime, ARRAY, Text, ForeignKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

EMBEDDING_SIZE = 1536  # Dimension of the embedding vectors


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered: Mapped[bool] = mapped_column(default=False)

    # Relationships
    tasks: Mapped[List["Task"]] = relationship(back_populates="project")
    meetings: Mapped[List["Meeting"]] = relationship(back_populates="project_ref")


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
    role: Mapped[str] = mapped_column(String(100))
    skills: Mapped[List[str]] = mapped_column(ARRAY(String))

    # Relationship for Tasks
    tasks: Mapped[List["Task"]] = relationship(back_populates="owner")


class Meeting(Base):
    __tablename__ = "meetings"

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255))
    date: Mapped[datetime] = mapped_column(DateTime)
    project_name: Mapped[str] = mapped_column(ForeignKey("projects.name"))

    project_ref: Mapped["Project"] = relationship(back_populates="meetings")
    chunks: Mapped[List["MeetingChunk"]] = relationship(back_populates="meeting")


class MeetingChunk(Base):
    __tablename__ = "meeting_chunks"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.meeting_id")
    )
    text_content: Mapped[str] = mapped_column(Text)

    # Using pgvector for embeddings (requires 'pip install pgvector')
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(dim=EMBEDDING_SIZE))

    # FKs to Developers (Speakers)
    speaker_names: Mapped[List[str]] = mapped_column(ARRAY(String))

    meeting: Mapped["Meeting"] = relationship(back_populates="chunks")


class Note(Base):
    __tablename__ = "notes"

    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category_name: Mapped[str] = mapped_column()
    project_name: Mapped[str] = mapped_column()
    author: Mapped[str] = mapped_column(String(255))
    note_text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(dim=EMBEDDING_SIZE))
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Composite Foreign Key to CategoryMap
    __table_args__ = (
        ForeignKeyConstraint(
            ["category_name", "project_name"],
            ["category_maps.name", "category_maps.project_name"],
        ),
    )


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.name"))
    owner_id: Mapped[str] = mapped_column(ForeignKey("developers.name"))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50)
    )  # e.g., 'todo', 'in_progress', 'done'

    # Polymorphic-lite reference
    source_type: Mapped[str] = mapped_column(String(20))  # 'note' or 'meeting'
    source_id: Mapped[int] = mapped_column()

    project: Mapped["Project"] = relationship(back_populates="tasks")
    owner: Mapped["Developer"] = relationship(back_populates="tasks")
