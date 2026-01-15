from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
import uuid
from pydantic import BaseModel

# --- PROJECT SCHEMAS ---


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    delivered: bool = False


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime


# --- DEVELOPER SCHEMAS ---


class DeveloperBase(BaseModel):
    name: str
    role: str = Field(..., max_length=100)
    skills: List[str] = []


class DeveloperCreate(DeveloperBase):
    pass


class Developer(DeveloperBase):
    model_config = ConfigDict(from_attributes=True)


# --- CATEGORY MAP SCHEMAS ---


class CategoryMapBase(BaseModel):
    name: str
    project_name: str
    type: str = Field(..., max_length=50)


class CategoryMapCreate(CategoryMapBase):
    pass


class CategoryMap(CategoryMapBase):
    model_config = ConfigDict(from_attributes=True)


# --- MEETING & CHUNK SCHEMAS ---


class MeetingChunkBase(BaseModel):
    text_content: str
    embedding: Optional[List[float]] = None
    speaker_names: List[str] = []


class MeetingChunkCreate(MeetingChunkBase):
    meeting_id: uuid.UUID


class MeetingChunk(MeetingChunkBase):
    model_config = ConfigDict(from_attributes=True)
    chunk_id: uuid.UUID


class MeetingBase(BaseModel):
    title: str = Field(..., max_length=255)
    date: datetime
    project_name: str


class MeetingCreate(MeetingBase):
    pass


class Meeting(MeetingBase):
    model_config = ConfigDict(from_attributes=True)
    meeting_id: uuid.UUID


# --- NOTE SCHEMAS ---


class NoteBase(BaseModel):
    category_name: str
    project_name: str
    author: str = Field(..., max_length=255)
    note_text: str
    embedding: Optional[List[float]] = None
    date: datetime = Field(default_factory=datetime.utcnow)


class NoteCreate(NoteBase):
    pass


class Note(NoteBase):
    model_config = ConfigDict(from_attributes=True)
    note_id: uuid.UUID


# --- TASK SCHEMAS ---


class TaskBase(BaseModel):
    description: str
    status: str = "todo"
    source_type: str = Field(..., description="'note' or 'meeting'")
    source_id: int


class TaskCreate(TaskBase):
    project_id: str
    owner_id: str


class Task(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    task_id: uuid.UUID
    project_id: str
    owner_id: str
