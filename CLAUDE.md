# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Is Mind-Trace

A VS Code extension that lets developers capture, transcribe, search, and summarize meeting notes and code-level annotations directly inside the editor. Three layers communicate via postMessage and HTTP:

- **Extension host** (`src/`) — TypeScript, handles VS Code API interactions
- **Webview UI** (`webview-ui/`) — React 19 + Vite 7 + TailwindCSS 4, built separately
- **Backend** (`backend/`) — Python 3.13 FastAPI on `127.0.0.1:8000`, PostgreSQL + pgvector

## Development Commands

### Extension (root)
```bash
npm run compile       # One-time webpack build → dist/extension.js
npm run watch         # Webpack watch mode (used during development)
npm run lint          # ESLint on src/
npm test              # Run extension tests (requires compile + lint first)
```

### Webview UI (`webview-ui/`)
```bash
npm run dev           # Vite dev server (browser preview only, not in VS Code)
npm run build         # tsc + vite build → webview-ui/dist/ (extension reads from here)
npm run lint          # ESLint on webview-ui/src/
```

### Backend (`backend/`)
```bash
# Start server (run from repo root or backend/)
python -m app.__main__

# Database — start PostgreSQL container (port 5434)
docker compose -f backend/docker/postgres/compose.yaml up -d

# Run Alembic migrations (note: migrations folder is named "almebic" — typo in the repo)
alembic -c backend/alembic.ini upgrade head
```

## Architecture Overview

### Communication Flow
```
Webview (React) → postMessage → extension utilities.ts → axios HTTP → FastAPI backend → PostgreSQL
```

The webview uses `webview-ui/src/utilities/vscodeApi.ts` (a `postMessage` singleton with browser fallback). The extension's `utilities.ts` routes messages by `command` field and calls the backend via axios.

### Backend Structure
- `backend/app/__main__.py` — FastAPI app factory, registers all routers
- `backend/app/apis/` — Route handlers: `meeting_apis`, `notes_apis`, `authentication_apis`, `llm_apis`
- `backend/core/database/` — SQLAlchemy models, Pydantic schemas (`tables_data.py`), async repos, auth helpers
- `backend/core/audio_pipelines/` — `MeetingPipeline.py` (VAD → Diarization → Whisper → Summarize), `db_handling.py` (saves results)
- `backend/core/rag/` — LangChain-based RAG pipeline using local Ollama models
- `backend/core/notes/` — `note_manager.py` for note CRUD with embedding generation

### RAG / LLM
The `/llms/send_query` route runs the RAG pipeline (`core/rag/pipeline.py`): hybrid vector + keyword search over notes/meetings, then streams an answer from a local Ollama LLM. Default models: `mxbai-embed-large` (embeddings), `llama3.2` (generation). Configured via `core/rag/llm_config.py` and `core/rag/models.py`.

### Authentication
Email-based OTP flow: `/auth/send_otp` sends a 6-digit code via SMTP, `/auth/register_user` creates a `Company` (keyed by email domain) + `Employee`. Passwords are bcrypt-hashed. The `email` header is used to identify the current user in protected routes (e.g. `/notes/save_note`).

### Multi-tenant Data Model
All core entities (`Project`, `Meeting`, `Note`, `Task`, `Employee`) belong to a `Company` via `company_id`. The `Company` is created automatically from the email domain on first registration.

### Env Files
- `backend/.env` — `HF_TOKEN` (HuggingFace, for pyannote speaker diarization), `MIND_TRACE_EMAIL`, `MIND_TRACE_PASSWORD` (SMTP credentials)
- `backend/docker/postgres/postgres.env` — DB credentials loaded by `DatabaseConfigLoader`

## Key Known Issues

- `backend/almebic/` — folder name is a typo (should be `alembic`)
- Embedding size mismatch: `EMBEDDING_SIZE = 1024` for `Note.embedding` and `Employee.voice_print`, but `MeetingChunk.embedding` uses 384-dim (matching `all-MiniLM-L6-v2`)
- Search and AI Summary webview panels still use mock data — not connected to backend
- `app/notes/` directory exists but is empty; notes routing goes through `notes_apis.py`
- `Views/` and `Panels/` directories in webview-ui contain duplicate components (ongoing refactor)
