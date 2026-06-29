import os
from pathlib import Path

from core.audio_pipelines import db_handling
from core.database import authentication, tables_data
from core.database.postgresDatabase import PostgresDatabase
from core.database.repos import (
    CompanyRepository,
    MeetingRepository,
    ProjectRepository,
)
from fastapi import APIRouter, Body, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_PATH = BASE_DIR / "temp" / "audio"

router = APIRouter()

# cache of meetings (with their chunks) keyed by company_id.
# populated at startup so the meeting tab can be served without re-hitting the
_MEETINGS_CACHE: dict[int, list[dict]] = {}


def _serialize_meeting(meeting, chunks) -> dict:
    """Build a JSON-safe meeting record (chunks included, embeddings excluded)."""
    return {
        "id": meeting.id,
        "title": meeting.title,
        "date": meeting.date.isoformat() if meeting.date else None,
        "duration_sec": meeting.duration_sec,
        "language": meeting.language,
        "project_name": meeting.project_name,
        "meta": meeting.meta,
        "company_id": meeting.company_id,
        "chunks": [
            {
                "id": chunk.id,
                "raw_text": chunk.raw_text,
                "summary_text": chunk.summary_text,
                "start_time_sec": chunk.start_time_sec,
                "end_time_sec": chunk.end_time_sec,
                "speaker_names": chunk.speaker_names,
                "meta": chunk.meta,
            }
            for chunk in (chunks or [])
        ],
    }


async def startup_event():
    # start with an empty cache; each company's meetings are loaded lazily on
    # the first GET /meetings request for that company (never all companies).
    _MEETINGS_CACHE.clear()
    print("Meetings cache initialized (lazy per-company loading)")


async def shutdown_event():
    # 1. cleanup all temp files
    path = TEMP_PATH
    if path.is_dir():
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    item.unlink()
                except (PermissionError, OSError) as e:
                    return JSONResponse(status_code=500, content={"error": str(e)})
    return {"message": "Shutdown cleanup completed successfully"}


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/meetings")
async def get_meetings(email: str = Header(...)):
    # serve only the requesting user's company meetings; load that company's
    # meetings from the DB lazily on first request, then serve from cache.
    domain = authentication.get_email_domain(email)
    db = PostgresDatabase()
    company = await CompanyRepository(db.get_session_maker()).get_by_domain(domain)
    if company is None:
        print("couldn't find company for domain:", domain)
        return []
    if company.id not in _MEETINGS_CACHE:
        repo = MeetingRepository(db.get_session_maker())
        meetings = await repo.get_all_by_company(company.id)
        _MEETINGS_CACHE[company.id] = [
            _serialize_meeting(meeting, meeting.chunks) for meeting in meetings
        ]
        print(
            "loaded",
            len(_MEETINGS_CACHE[company.id]),
            "meetings from db for company:",
            company.name,
        )
    return _MEETINGS_CACHE[company.id]


@router.get("/projects")
async def get_projects(email: str = Header(...)):
    # return the project names belonging to the requesting user's company
    domain = authentication.get_email_domain(email)
    db = PostgresDatabase()
    company = await CompanyRepository(db.get_session_maker()).get_by_domain(domain)
    if company is None:
        return []
    projects = await ProjectRepository(db.get_session_maker()).get_all_by_company(
        company.id
    )
    return [project.name for project in projects]


@router.post("/create_project")
async def create_project(data: dict = Body(...)):
    # create a new project for the current user's company
    domain = authentication.get_email_domain(data["email"])
    db = PostgresDatabase()
    company = await CompanyRepository(db.get_session_maker()).get_by_domain(domain)
    if company is None:
        return JSONResponse(
            status_code=404, content={"error": "Company not found for user"}
        )
    try:
        project_data = tables_data.Project(
            name=data["projectName"],
            description=data.get("description"),
            created_at=data.get("creationDate"),
            company_id=company.id,
        )
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    project_repo = ProjectRepository(db.get_session_maker())
    project_id = await project_repo.create(project_data)
    if project_id is False:
        return JSONResponse(
            status_code=500, content={"error": "Failed to create project"}
        )
    return {
        "message": f"Successfully created project: {data['projectName']}",
        "id": project_id,
    }


class FileRequest(BaseModel):
    filePath: str


@router.post("/save_meeting_audio")
async def save_meeting_audio(file_request: FileRequest):
    filePath = file_request.filePath
    try:
        filename = os.path.basename(filePath)
        TEMP_PATH.mkdir(parents=True, exist_ok=True)
        target_path = TEMP_PATH / filename

        with open(filePath, "rb") as f:
            contents = f.read()

        target_path.write_bytes(contents)
        print(f"saved file: {filename}")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"filename": filename, "size": len(contents)}


@router.post("/close_modal")
async def close_modal(file: FileRequest):
    print(f"Received request to close modal for file: {file.filePath}")
    target_file = TEMP_PATH / file.filePath
    if os.path.exists(target_file):
        os.remove(target_file)
        return {"message": "Modal closed successfully"}
    return {"message": "File not found"}


@router.post("/process_meeting")
async def process_meeting(data: dict = Body(...)):
    domain = authentication.get_email_domain(data["email"])
    db = PostgresDatabase()
    CompanyRepo = CompanyRepository(db.get_session_maker())
    company = await CompanyRepo.get_by_domain(domain)
    valid_process = await db_handling.process_meeting_audio(
        file_path=str(TEMP_PATH / data["filename"]),
        language=data["language"],
        project_name=data["projectName"],
        title=data["title"],
        date=data["date"],
        company_id=company.id,
    )
    del CompanyRepo
    if valid_process is False:
        del db
        return JSONResponse(
            status_code=500, content={"error": "Failed to process meeting"}
        )
    # invalidate this company's cache so the new meeting is picked up next fetch
    _MEETINGS_CACHE.pop(company.id, None)
    del db
    # remove temp file
    print(f"Processing completed for file: {data['filename']}. Removing temp file.")
    target_file = TEMP_PATH / data["filename"]
    if os.path.exists(target_file):
        os.remove(target_file)
    return {"message": f"Successfully processed meeting: {data['title']}"}
