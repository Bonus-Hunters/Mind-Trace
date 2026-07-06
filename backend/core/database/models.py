from datetime import datetime
from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from utils.constants import EMBEDDING_SIZE, VOICE_PRINT_SIZE


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Relationships
    notes: Mapped[List["Note"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    employees: Mapped[List["Employee"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    projects: Mapped[List["Project"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    meetings: Mapped[List["Meeting"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    category_maps: Mapped[List["CategoryMap"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    employee_projects: Mapped[List["EmployeeProject"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class CategoryMap(Base):
    __tablename__ = "category_maps"
    id: Mapped[int] = mapped_column(primary_key=True, server_default=Identity())

    name: Mapped[str] = mapped_column()
    project_name: Mapped[str] = mapped_column(ForeignKey("projects.name"))
    type: Mapped[str] = mapped_column(String(50))
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )
    __table_args__ = (
        UniqueConstraint(
            "name",
            "project_name",
            "company_id",
            name="uq_category_name_project_company",
        ),
    )

    # Relationship
    company: Mapped["Company"] = relationship(back_populates="category_maps")


class EmployeeProject(Base):
    __tablename__ = "employee_projects"
    id: Mapped[int] = mapped_column(primary_key=True, server_default=Identity())

    # Foreign keys pointing to your primary keys

    employee_name: Mapped[str] = mapped_column(
        ForeignKey("employees.name", ondelete="CASCADE")
    )
    project_name: Mapped[str] = mapped_column(
        ForeignKey("projects.name", ondelete="CASCADE")
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )
    __table_args__ = (
        UniqueConstraint(
            "employee_name",
            "project_name",
            "company_id",
            name="uq_name_project_company",
        ),
    )
    # Relationship
    company: Mapped["Company"] = relationship(back_populates="employee_projects")


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(
        primary_key=True, server_default=Identity(), autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    delivered: Mapped[Optional[bool]] = mapped_column(default=False)
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

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
    company: Mapped["Company"] = relationship(back_populates="projects")


class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True, server_default=Identity())
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(60))
    skills: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    voice_print: Mapped[Optional[List[float]]] = mapped_column(
        Vector(dim=VOICE_PRINT_SIZE), nullable=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    assigned_projects: Mapped[List["Project"]] = relationship(
        secondary="employee_projects",  # Matches the __tablename__ of the link table
        back_populates="team_members",
    )
    # Relationships
    tasks: Mapped[List["Task"]] = relationship(back_populates="owner")
    company: Mapped["Company"] = relationship(back_populates="employees")


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
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    # relations
    project_ref: Mapped["Project"] = relationship(back_populates="meetings")
    chunks: Mapped[List["MeetingChunk"]] = relationship(back_populates="meeting")
    company: Mapped["Company"] = relationship(back_populates="meetings")


class MeetingChunk(Base):
    __tablename__ = "meeting_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
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
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(dim=EMBEDDING_SIZE))

    # FKs to Employees (Speakers)
    speaker_names: Mapped[List[str]] = mapped_column(ARRAY(String))

    meeting: Mapped["Meeting"] = relationship(back_populates="chunks")


# CHECK: filename or filepath???
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
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    function: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    module: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    line_number: Mapped[Optional[int]] = mapped_column(None, nullable=True)
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, default=dict, server_default="{}", nullable=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    # relation
    project: Mapped["Project"] = relationship(
        back_populates="notes", foreign_keys=[project_name]
    )
    company: Mapped["Company"] = relationship(back_populates="notes")


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
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")
    owner: Mapped["Employee"] = relationship(back_populates="tasks")
    company: Mapped["Company"] = relationship(back_populates="tasks")
