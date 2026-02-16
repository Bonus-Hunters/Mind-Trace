import asyncio
import os
from pathlib import Path
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.audio_pipelines import db_handling
import pprint

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_PATH = BASE_DIR / "temp" / "audio"

router = APIRouter()


async def startup_event():
    # 1. retrieve all meeting data ffrom db and cache it
    pass


async def shutdown_event():

    # 1. cleanup all temp files
    path = f"{TEMP_PATH}"
    if path.is_dir():
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    item.unlink()
                except PermissionError or OSError as e:
                    return JSONResponse(status_code=500, content={"error": str(e)})
    return {"message": "Shutdown cleanup completed successfully"}


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


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

    valid_process = await db_handling.process_meeting_audio(
        file_path=str(TEMP_PATH / data["filename"]),
        language=data["language"],
        project_name=data["projectName"],
        title=data["title"],
        date=data["date"],
    )

    if not valid_process:
        return JSONResponse(
            status_code=500, content={"error": "Failed to process meeting"}
        )
    return {"message": f"Successfully processed meeting: {data['title']}"}
