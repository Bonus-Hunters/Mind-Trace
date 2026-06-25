from datetime import datetime

from core.rag.models import EMBED_MODEL, LLM_MODEL
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    projectName: str


class SearchResultItem(BaseModel):
    id: str
    title: str
    snippet: str
    type: str  # "function", "file", "feature", "meeting"
    filePath: str | None = None
    tags: list[str] = []
    similarity: float
    timestamp: str


@router.get("/get_local_llms")
async def get_llms():
    import ollama

    print("---   fetching local ollama llms ---")
    try:
        response = ollama.list()
        raw_models = getattr(response, "models", None)
        if raw_models is None and isinstance(response, dict):
            raw_models = response.get("models", [])
        raw_models = raw_models or []

        model_names: list[str] = []
        for model in raw_models:
            name = (
                getattr(model, "model", None)
                or getattr(model, "name", None)
                or (model.get("model") if isinstance(model, dict) else None)
                or (model.get("name") if isinstance(model, dict) else None)
            )
            if not name:
                continue

            is_llm = True
            try:
                info = ollama.show(name)
                capabilities = (
                    getattr(info, "capabilities", None)
                    or (info.get("capabilities") if isinstance(info, dict) else None)
                    or []
                )
                capabilities = [str(c).lower() for c in capabilities]
                if capabilities:
                    is_llm = "completion" in capabilities or "chat" in capabilities
                else:
                    is_llm = "embed" not in name.lower()
            except Exception:
                is_llm = "embed" not in name.lower()

            if is_llm:
                model_names.append(name)

        print(f"---   local ollama llms: {model_names}")
        return model_names
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/send_query")
async def send_query(request: QueryRequest):
    from core.rag.llm_config import LLMConfig
    from core.rag.pipeline import mind_trace_query

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


@router.post("/search")
async def search(request: QueryRequest):
    """Search for notes and meetings using RAG pipeline."""
    from core.rag.llm_config import LLMConfig
    from core.rag.pipeline import search

    try:
        embed_cfg = LLMConfig(
            provider="ollama",
            model=EMBED_MODEL,
        )

        # Call the search function from pipeline
        docs = await search(
            query=request.query,
            project_name=request.projectName,
            embed_config=embed_cfg,
        )

        # Convert Document objects to SearchResultItem objects
        results: list[SearchResultItem] = []
        for idx, doc in enumerate(docs):
            metadata = doc.metadata or {}
            source = metadata.get("source", "unknown")

            # Determine result type and title
            if source == "meeting":
                result_type = "meeting"
                title = metadata.get("title", "Meeting")
            else:  # note
                result_type = "feature"
                title = metadata.get("title", "Note")

            # Extract relevant fields
            file_path = metadata.get("file_name")
            tags = metadata.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            similarity_score = metadata.get("score", 0.0)
            if isinstance(similarity_score, str):
                try:
                    similarity_score = float(similarity_score)
                except (ValueError, TypeError):
                    similarity_score = 0.8

            # Normalize similarity to 0-1git range
            similarity_score = max(0.0, min(1.0, similarity_score / 1.0))

            # Get timestamp
            timestamp_str = metadata.get("date")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str).isoformat()
                except (ValueError, TypeError):
                    timestamp = datetime.now().isoformat()
            else:
                timestamp = datetime.now().isoformat()

            result = SearchResultItem(
                id=f"result-{idx}",
                title=title,
                snippet=doc.page_content[:200] if doc.page_content else "",
                type=result_type,
                filePath=file_path,
                tags=tags if isinstance(tags, list) else [],
                similarity=similarity_score,
                timestamp=timestamp,
            )
            results.append(result)

        return {"results": results}
    except Exception as e:
        print(f"Search error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
