import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

TEMP_PATH = "../../Temp"

app = FastAPI()

origins = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/save_meeting_audio")
async def save_meeting_audio(file: UploadFile = File(...)):
    try:
        filename = file.filename
        contents = await file.read()
        # to save it tmporarily
        temp_path = f"{TEMP_PATH}/Audio/{filename}"

        with open(temp_path, "wb") as buffer:
            buffer.write(contents)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"filename": filename, "size": len(contents)}


@app.post("/close_modal")
async def close_modal(filename: str):
    if os.path.exists(f"{TEMP_PATH}/Audio/{filename}"):
        os.remove(f"{TEMP_PATH}/Audio/{filename}")
    return {"message": "Modal closed successfully"}


@app.post("/process-meeting")
async def process_meeting():
    pass
