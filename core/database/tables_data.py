from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
import uuid
from pydantic import BaseModel
from utils.constants import EMBEDDING_SIZE

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
    role: Optional[str] = Field(..., max_length=100)
    skills: Optional[List[str]] = []


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
    embedding: List[float] = Field(
        ..., min_items=EMBEDDING_SIZE, max_items=EMBEDDING_SIZE
    )
    speaker_names: List[str] = []
    meeting_id: int


class MeetingChunkCreate(MeetingChunkBase):
    pass


class MeetingChunk(MeetingChunkBase):
    model_config = ConfigDict(from_attributes=True)


class MeetingBase(BaseModel):
    title: str = Field(..., max_length=255)
    date: datetime
    project_name: str


class MeetingCreate(MeetingBase):
    pass


class Meeting(MeetingBase):
    model_config = ConfigDict(from_attributes=True)


# --- NOTE SCHEMAS ---


class NoteBase(BaseModel):
    project_name: str = Field(..., max_length=255)
    author: str = Field(..., max_length=255)
    note_text: str
    embedding: List[float] = Field(
        ..., min_items=EMBEDDING_SIZE, max_items=EMBEDDING_SIZE
    )
    type: str = Field(..., max_length=50)
    tags: Optional[str] = Field(None, max_length=255)
    function: Optional[str] = None
    file_name: Optional[str] = Field(None, max_length=50)
    module: Optional[str] = Field(None, max_length=50)


class NoteCreate(NoteBase):
    pass


class Note(NoteBase):
    date: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(from_attributes=True)


# --- TASK SCHEMAS ---


class TaskBase(BaseModel):
    description: str
    status: str = "todo"
    source_type: str = Field(..., description="'note' or 'meeting'")
    project_name: str
    assignee_name: str


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    model_config = ConfigDict(from_attributes=True)
