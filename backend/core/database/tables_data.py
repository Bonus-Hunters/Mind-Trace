from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from utils.constants import EMBEDDING_SIZE


class Company(BaseModel):
    name: str = Field(..., max_length=255)
    domain: str = Field(..., max_length=255)
    model_config = ConfigDict(from_attributes=True)


class Project(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    delivered: bool = False
    created_at: datetime
    company_id: int
    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    description: Optional[str] = None
    delivered: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)


class EmployeeProject(BaseModel):
    employee_name: str
    project_name: str
    company_id: int

    model_config = ConfigDict(from_attributes=True)


"""
    TODO: 
        - make email, password optional since not every employee need to 
            have an account [AKA using the extension].
        - before user login check if he's in the database [his name]    
            [issue: name in db might be different than what user write.]
"""


class Employees(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = Field(..., max_length=100)
    skills: Optional[List[str]] = []
    voice_print: Optional[List[float]] = Field(
        ..., min_items=EMBEDDING_SIZE, max_items=EMBEDDING_SIZE
    )
    company_id: int
    model_config = ConfigDict(from_attributes=True)


class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(..., max_length=255)
    role: Optional[str] = Field(..., max_length=100)
    skills: Optional[List[str]] = []
    model_config = ConfigDict(from_attributes=True)


class CategoryMap(BaseModel):
    name: str
    project_name: str
    type: str = Field(..., max_length=50)
    company_id: int
    model_config = ConfigDict(from_attributes=True)


class CategoryMapUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=50)
    model_config = ConfigDict(from_attributes=True)


class MeetingChunk(BaseModel):
    raw_text: str
    summary_text: str
    start_time_sec: float
    end_time_sec: float
    embedding: List[float] = Field(..., min_items=384, max_items=384)
    speaker_names: List[str] = []
    meeting_id: int
    meta: Optional[Dict[str, Any]]
    model_config = ConfigDict(from_attributes=True)


class MeetingChunkUpdate(BaseModel):
    raw_text: Optional[str] = None
    summary_text: Optional[str] = None
    start_time_sec: Optional[float] = None
    end_time_sec: Optional[float] = None
    embedding: Optional[List[float]] = Field(
        None, min_items=EMBEDDING_SIZE, max_items=EMBEDDING_SIZE
    )
    speaker_names: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)


class Meeting(BaseModel):
    title: str = Field(..., max_length=255)
    date: datetime
    language: str = Field(None, max_length=50)
    duration_sec: Optional[float] = None
    project_name: str
    meta: Optional[Dict[str, Any]]
    company_id: int
    # tags: Optional[str] = Field(None, max_length=255)
    model_config = ConfigDict(from_attributes=True)


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    meta: Optional[Dict[str, Any]] = None
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
    company_id: int
    model_config = ConfigDict(from_attributes=True)


class NoteUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=255)
    function: Optional[str] = None
    file_name: Optional[str] = Field(None, max_length=50)
    module: Optional[str] = Field(None, max_length=50)
    meta: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)


class Task(BaseModel):
    description: str
    status: str = "todo"
    source_type: str = Field(..., description="'note' or 'meeting'")
    project_name: str
    assignee_name: str
    company_id: int

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    assignee_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
