from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    String,
    ForeignKey,
    DateTime,
    ARRAY,
    Text,
    ForeignKeyConstraint,
    Float,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from utils.constants import EMBEDDING_SIZE
from sqlalchemy.dialects.postgresql import JSONB


class Base(DeclarativeBase):
    pass


class CategoryMap(Base):
    __tablename__ = "category_maps"

    name: Mapped[str] = mapped_column(primary_key=True)
    project_name: Mapped[str] = mapped_column(
        ForeignKey("projects.name"), primary_key=True
    )
    type: Mapped[str] = mapped_column(String(50))


class EmployeeProject(Base):
    __tablename__ = "employee_projects"
    # Foreign keys pointing to your primary keys
    employee_name: Mapped[str] = mapped_column(
        ForeignKey("employees.name", ondelete="CASCADE"), primary_key=True
    )
    project_name: Mapped[str] = mapped_column(
        ForeignKey("projects.name", ondelete="CASCADE"), primary_key=True
    )


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered: Mapped[bool] = mapped_column(default=False)
    tags: Mapped[str] = mapped_column(String(255), nullable=True)

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
    team_members: Mapped[List["Employee"]] = relationship(
        secondary="employee_projects",
        back_populates="assigned_projects",
    )


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=True)
    skills: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    voice_print: Mapped[Optional[List[float]]] = mapped_column(
        Vector(dim=EMBEDDING_SIZE), nullable=True
    )
    assigned_projects: Mapped[List["Project"]] = relationship(
        secondary="employee_projects",  # Matches the __tablename__ of the link table
        back_populates="team_members",
    )
    # Relationships
    tasks: Mapped[List["Task"]] = relationship(back_populates="owner")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    date: Mapped[datetime] = mapped_column(DateTime)
    project_name: Mapped[str] = mapped_column(ForeignKey("projects.name"))
    duration_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50))
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=True
    )

    # relations
    project_ref: Mapped["Project"] = relationship(back_populates="meetings")
    chunks: Mapped[List["MeetingChunk"]] = relationship(back_populates="meeting")


class MeetingChunk(Base):
    __tablename__ = "meeting_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE")
    )
    raw_text: Mapped[str] = mapped_column(Text)
    summary_text: Mapped[str] = mapped_column(Text)

    start_time_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_time_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=True
    )

    # Using pgvector for embeddings (requires 'pip install pgvector')
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(dim=384))

    # FKs to Employees (Speakers)
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
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=True
    )

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
        ForeignKey("employees.name", ondelete="SET NULL")
    )
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50)
    )  # e.g., 'todo', 'in_progress', 'done'

    # Polymorphic-lite reference
    source_type: Mapped[str] = mapped_column(String(20))  # 'note' or 'meeting'

    project: Mapped["Project"] = relationship(back_populates="tasks")
    owner: Mapped["Employee"] = relationship(back_populates="tasks")
