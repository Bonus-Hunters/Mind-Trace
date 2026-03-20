from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from utils.constants import EMBEDDING_SIZE


class Project(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    delivered: bool = False
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Developer(BaseModel):
    name: str
    role: Optional[str] = Field(..., max_length=100)
    skills: Optional[List[str]] = []

    model_config = ConfigDict(from_attributes=True)


class CategoryMap(BaseModel):
    name: str
    project_name: str
    type: str = Field(..., max_length=50)
    model_config = ConfigDict(from_attributes=True)


class MeetingChunk(BaseModel):
    text_content: str
    embedding: List[float] = Field(
        ..., min_items=EMBEDDING_SIZE, max_items=EMBEDDING_SIZE
    )
    speaker_names: List[str] = []
    meeting_id: int

    model_config = ConfigDict(from_attributes=True)


class Meeting(BaseModel):
    title: str = Field(..., max_length=255)
    date: datetime
    project_name: str
    meta: Optional[Dict[str, Any]]
    model_config = ConfigDict(from_attributes=True)


class Note(BaseModel):
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

    date: datetime = Field(default_factory=datetime.utcnow)
    meta: Optional[Dict[str, Any]]
    model_config = ConfigDict(from_attributes=True)


class Task(BaseModel):
    description: str
    status: str = "todo"
    source_type: str = Field(..., description="'note' or 'meeting'")
    project_name: str
    assignee_name: str

    model_config = ConfigDict(from_attributes=True)
