import os
from pathlib import Path
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.audio_pipelines import db_handling
from core.database.tables_data import NoteCreate
from core.notes.note_manager import DatabaseNoteManager
from core.database.authentication import get_current_author
from utils.enums import NoteType

router = APIRouter()


@router.post("/save_note")
async def save_note(note_data: NoteCreate, email: str = Header()):
    try:
        author = await get_current_author(email)
        if author:
            company_id = int(author.company_id)
            noteManager = DatabaseNoteManager()
            await noteManager.add_note(note_data, author.email, company_id)
        else:
            return JSONResponse(
                status_code=500, content={"error": "Couldn't Retrieve User's Entry"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        del noteManager
