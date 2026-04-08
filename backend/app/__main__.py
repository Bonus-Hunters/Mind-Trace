from app.apis import authentication_apis, meeting_apis, notes_apis, llm_apis
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from core.database.postgresDatabase import PostgresDatabase
from core.config_loader import DatabaseConfigLoader, ConfigLoader


# init singleton  objects to stay in memory
db = PostgresDatabase()
db_config_loader = DatabaseConfigLoader()
config_loader = ConfigLoader()


def include_routers(app: FastAPI):
    app.include_router(meeting_apis.router)
    app.include_router(authentication_apis.router, prefix="/auth")
    app.include_router(notes_apis.router, prefix="/notes")
    app.include_router(llm_apis.router, prefix="/llms")


def create_server():
    app = FastAPI()
    include_routers(app)
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
