from fastapi import FastAPI
from app.audio_related import meeting
import uvicorn
from fastapi.middleware.cors import CORSMiddleware


def include_router(app: FastAPI):
    app.include_router(meeting.router)


def create_server():
    app = FastAPI()
    include_router(app)
    return app


app = create_server()
if __name__ == "__main__":
    origins = [
        "http://localhost:8000",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uvicorn.run("app.__main__:app", host="127.0.0.1", port=8000, reload=True)
