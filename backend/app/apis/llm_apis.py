import os
from pathlib import Path
from core.rag.models import EMBED_MODEL, LLM_MODEL
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.audio_pipelines import db_handling
from core.database.tables_data import NoteCreate
from core.notes.note_manager import DatabaseNoteManager
from core.database.authentication import get_current_author
from utils.enums import NoteType

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    projectName: str


@router.get("/get_local_llms")
async def get_llms():
    import ollama

    try:

        response = ollama.list()
        model_names = [model["name"] for model in response["models"]]
        return model_names
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/send_query")
async def send_query(request: QueryRequest):
    from core.rag.pipeline import mind_trace_query
    from core.rag.llm_config import LLMConfig

    try:
        llm_cfg = LLMConfig(
            provider="ollama",
            model=LLM_MODEL,
            temperature=0.8,
        )
        embed_cfg = LLMConfig(
            provider="ollama",
            model=EMBED_MODEL,
        )

        response_chunks = []
        full_response = await mind_trace_query(
            request.query,
            request.projectName,
            llm_cfg,
            embed_cfg,
        )
        # full_response = "".join(response_chunks)
        print(f"---   output:: {full_response}")
        return {"response": full_response}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
