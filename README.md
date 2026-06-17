# Mind-Trace

A **VS Code extension** that lets developers capture, transcribe, search, and summarize
**meeting notes** and **code-level annotations** directly inside the editor. Notes and
meeting transcripts are embedded as vectors and made searchable through a local
Retrieval-Augmented Generation (RAG) assistant — everything runs locally (PostgreSQL +
Ollama), so source context never leaves the machine.

This README is the single, comprehensive reference for the project: what it is, how the
three layers fit together, every message/endpoint, the data model, runtime flows, and how
to build/run each piece. The sequence diagrams in [`diagrams/`](diagrams/) visualize the
same flows at four levels of detail.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture & Diagrams](#architecture--diagrams)
3. [Repository Layout](#repository-layout)
4. [Message Protocol (Webview ↔ Extension)](#message-protocol-webview--extension)
5. [Backend API Reference](#backend-api-reference)
6. [Runtime Flows](#runtime-flows)
7. [Data Model](#data-model)
8. [External Services](#external-services)
9. [Build, Develop & Run](#build-develop--run)
10. [Environment Files](#environment-files)
11. [Known Issues](#known-issues)

---

## System Overview

Mind-Trace is made of **three decoupled layers** that communicate via `postMessage`
(within VS Code) and HTTP (to the backend):

| Layer | Path | Stack | Responsibility |
|-------|------|-------|----------------|
| **Extension host** | `src/` | TypeScript, webpack | VS Code API, webview lifecycle, command registration, routes webview messages → backend via axios |
| **Webview UI** | `webview-ui/` | React 19, Vite 7, TailwindCSS 4 | All UI (login, notes, search, AI chat, meetings); talks to extension only via `postMessage` |
| **Backend** | `backend/` | Python 3.13, FastAPI on `127.0.0.1:8000`, PostgreSQL + pgvector | Auth, note/meeting persistence, embeddings, audio pipeline, hybrid search + RAG |

**Communication model:**

```
Webview (React) → postMessage → Extension (messages.ts) → axios HTTP → FastAPI → PostgreSQL / Ollama
```

The webview can also run standalone in a browser (Vite dev server) because
`webview-ui/src/utilities/vscodeApi.ts` falls back to a console mock when the VS Code API
is unavailable.

---

## Architecture & Diagrams

Four sequence diagrams in [`diagrams/`](diagrams/), each at an increasing level of detail.
The Mermaid sources (`.mmd`) live next to the PNGs so they can be edited and re-rendered
(see [Regenerating the diagrams](#regenerating-the-diagrams)).

### Level 1 — Architecture overview
The generic request/response round-trip across all three layers.

![Architecture overview](diagrams/01_architecture_overview.png)

### Level 2 — Main user flows
Auth, save note, search, and ask-the-assistant at a glance (message command + endpoint).

![Main user flows](diagrams/02_main_user_flows.png)

### Level 3 — Note save & RAG query, detailed
The two core flows with real function names and files.

![Note & RAG detail](diagrams/03_note_and_rag_detail.png)

### Level 4 — Full system (exhaustive)
Everything, including the meeting audio pipeline (VAD → diarization → Whisper → summarize).

![Full system detail](diagrams/04_full_system_detail.png)

---

## Repository Layout

```
Mind-Trace/
├── src/                              # Extension host (TypeScript)
│   ├── extension.ts                  # activate(), webview provider, command registration
│   ├── messages.ts                   # Message dispatcher (routes by command field)
│   └── Messages/
│       ├── authentication_messages.ts  # OTP send/verify/resend, auth-status
│       ├── saving_data_messages.ts     # save note/quick note, audio upload, close modal
│       ├── llm_messages.ts             # Ollama model list, change LLM, send query
│       └── helpers.ts                  # workspace folder name → projectName
│
├── webview-ui/                       # React webview (Vite + Tailwind)
│   └── src/
│       ├── App.tsx                   # Root: auth state + window "message" listener
│       ├── utilities/vscodeApi.ts    # postMessage singleton (browser fallback)
│       └── components/
│           ├── Views/                # LoginScreen, MainScreen, MeetingMinutesView
│           ├── NoteModal/            # AddNoteModal, QuickNoteModal
│           ├── Panels/               # AISummaryPanel (RAG chat)
│           └── SearchPanel.tsx       # Hybrid search UI
│
├── backend/                         # FastAPI backend (Python 3.13)
│   ├── app/
│   │   ├── __main__.py              # App factory, router registration, uvicorn
│   │   └── apis/                    # meeting_apis, notes_apis, authentication_apis, llm_apis
│   ├── core/
│   │   ├── database/               # models.py (SQLAlchemy), tables_data.py (Pydantic),
│   │   │                           # repos.py, authentication.py
│   │   ├── notes/note_manager.py   # Note CRUD + embedding generation
│   │   ├── audio_pipelines/        # MeetingPipeline.py, db_handling.py
│   │   └── rag/                    # pipeline.py, search.py, llm_factory.py, llm_config.py,
│   │                               # models.py, prompts.py, context.py
│   ├── models/audio/              # SileroVAD, SpeakerDiarization, FasterWhisper, TextSummarizer
│   ├── docker/postgres/           # compose.yaml (port 5434), postgres.env
│   └── almebic/                   # Alembic migrations (folder name is a typo — see Known Issues)
│
├── diagrams/                       # Sequence diagrams (.mmd sources + .png renders)
├── dist/                           # Webpack output (extension.js)
└── README.md
```

---

## Message Protocol (Webview ↔ Extension)

The webview never calls the backend directly. It posts a `{ command, data }` message via
`vscode.postMessage(...)` (`webview-ui/src/utilities/vscodeApi.ts`); the extension's
`handleReceivedMessages()` in `src/messages.ts` dispatches on `command`.

### Webview → Extension

| Command | Handler (file) | Backend endpoint |
|---------|----------------|------------------|
| `react_ready` | `valid_user()` — authentication_messages.ts | *(local: checks stored auth)* |
| `sendOTP` | `_sendOTP()` — authentication_messages.ts | `POST /auth/send_otp` |
| `verifyOTP` | `_verifyOTP()` — authentication_messages.ts | `POST /auth/register_user` |
| `resendOTP` | `_resendOTP()` — authentication_messages.ts | `POST /resend_otp` |
| `saveNote` | `save_note()` — saving_data_messages.ts | `POST /notes/save_note` |
| `saveQuickNote` | `save_quick_note()` — saving_data_messages.ts | `POST /notes/save_note` |
| `selectAudioFile` | `handleFileSelection()` — saving_data_messages.ts | `POST /save_meeting_audio` |
| `closeAddNoteModal` | `closeAddNoteModal()` — saving_data_messages.ts | `POST /close_modal` |
| `getOllamaModels` | `get_local_Ollama_LLMs()` — llm_messages.ts | `GET /llms/get_local_llms` |
| `changeLLM` | `change_LLM()` — llm_messages.ts | *(stub)* |
| `send_query_to_llm` | `send_query_to_llm()` — llm_messages.ts | `POST /llms/send_query` |
| `send_search_query` | `_send_search_query()` — messages.ts | `POST /llms/search` |
| `close_panel` | *(inline)* — messages.ts | *(local: closes sidebar)* |

### Extension → Webview

`auth-status`, `otp-sent-success`, `otp-error`, `login-success`, `openQuickNote`,
`audioProcessingFinished`, `search_results`, `search_error`, `ollamaModels`,
`llm_response`, `llm_error`, `quickNoteSaved`, `quickNoteError`.

These are received by the `window.addEventListener("message", …)` handler in
`webview-ui/src/App.tsx` (and per-component listeners in `SearchPanel`, `AISummaryPanel`,
`MainScreen`, `LoginScreen`).

### VS Code commands (editor → extension)

| Command | Action |
|---------|--------|
| `Mind-Trace.runextension` | Open & focus the sidebar webview |
| `Mind-Trace.logout` | Clear `userEmail` (globalState) + `userAuthToken` (secrets) |
| `Mind-Trace.addNote` | Capture selected code context (function, file, line) → open Quick Note |

---

## Backend API Reference

All requests go to `http://127.0.0.1:8000`. Routers are registered in
`backend/app/__main__.py`. Protected note routes identify the user via the **`email` HTTP
header** (`get_current_author()` in `core/database/authentication.py`).

| Endpoint | Method | Payload | Notes |
|----------|--------|---------|-------|
| `/auth/send_otp` | POST | `{email, password, name}` | Generates a 6-digit OTP, sends via SMTP (provider chosen by email domain) |
| `/auth/register_user` | POST | `{email, password, name}` | Creates `Company` (by email domain) + `Employee`; bcrypt password |
| `/resend_otp` | POST | `{email}` | Re-sends OTP |
| `/notes/save_note` | POST | `{note_text, project_name, type, tags, function, file_name, module?, line_number, title?}` + `email` header | Embeds text (1024-dim) and inserts note |
| `/save_meeting_audio` | POST | `{filePath}` | Copies the audio file into `backend/core/temp/audio/` |
| `/process_meeting` | POST | `{filename, language, projectName, title, date, email, tags}` | Runs the meeting pipeline, persists meeting + chunks |
| `/close_modal` | POST | `{filePath}` | Deletes the temp audio file |
| `/llms/get_local_llms` | GET | — | Lists local Ollama models |
| `/llms/search` | POST | `{query, projectName}` | Hybrid search → `SearchResultItem[]` |
| `/llms/send_query` | POST | `{query, projectName}` | RAG: retrieve context → Ollama answer |

---

## Runtime Flows

### Authentication (email OTP)
1. Webview sends `sendOTP` → `POST /auth/send_otp`.
2. `authentication.py`: `generate_OTP()` + `send_email()` picks the SMTP server by domain
   (Gmail `:465` SSL, Outlook `:587` STARTTLS, Yahoo, iCloud…) and emails the code.
3. Webview shows the OTP modal; on submit sends `verifyOTP` → `POST /auth/register_user`.
4. Backend extracts the email domain, finds-or-creates a `Company` (keyed by domain),
   then creates an `Employee` with a bcrypt-hashed password.
5. Extension stores `userEmail` (globalState) + `userAuthToken` (secrets); webview shows
   the main screen. The `email` header identifies the user on every later protected call.

### Save note
1. From the editor, **Add Note** captures the selected code's function/file/line and opens
   the Quick Note modal; or the user fills the full **Add Note** form.
2. Webview sends `saveNote`/`saveQuickNote` → `POST /notes/save_note` (with `email` header).
3. `get_current_author(email)` resolves the `Employee` and `company_id`.
4. `DatabaseNoteManager.add_note()` embeds the text with `OllamaEmbeddings("mxbai-embed-large")`
   (1024-dim) and `NoteRepository.create()` inserts the `Note` (pgvector column).

### Meeting audio pipeline
1. `selectAudioFile` → `POST /save_meeting_audio` copies the file to `core/temp/audio/`.
2. `POST /process_meeting` → `db_handling.process_meeting_audio()` → `MeetingPipeline.process()`:
   - `load_models()` (lazy) → **SileroVAD** (voice activity) → **SpeakerDiarizer**
     (pyannote, needs `HF_TOKEN`) → **FasterWhisper** transcription with word timestamps.
   - Align words to speakers, merge consecutive same-speaker turns.
   - **TextSummarizer** chunks the dialogue, summarizes each chunk, and embeds it.
3. `MeetingRepository.create()` saves the `Meeting`; each chunk saved via
   `MeetingChunkRepository.create()` (embedding + speaker names + time range).
4. `closeAddNoteModal` → `POST /close_modal` removes the temp file.

### Search & RAG query
- **Search** (`POST /llms/search`) and **Ask** (`POST /llms/send_query`) both call
  `retrieve_hybrid()` in `core/rag/search.py`:
  1. **Vector search** — cosine distance (`<=>`) over note + meeting-chunk embeddings,
     filtered by `min_similarity`.
  2. **Keyword search** — `plainto_tsquery` full-text + `pg_trgm` trigram fallback.
  3. **Reciprocal Rank Fusion** merges both rankings → top 8 documents.
- **Search** maps results to `SearchResultItem[]` (title, snippet, similarity, tags, file).
- **Ask** additionally runs `build_context(docs)` then the `rag_chain`
  (`rag_prompt | OllamaLLM("llama3.2") | StrOutputParser`) to produce a grounded answer
  that "must answer strictly using the provided context."

---

## Data Model

All core entities belong to a `Company` via `company_id` (multi-tenant; the company is
created automatically from the email domain on first registration). SQLAlchemy models live
in `core/database/models.py`; Pydantic schemas in `core/database/tables_data.py`.

```
Company ─┬─< Employee
         ├─< Project ─┬─< Meeting ─< MeetingChunk
         │            ├─< Note
         │            └─< Task
         └─< (Meeting / Note / Task also carry company_id directly)
```

| Entity | Key fields |
|--------|-----------|
| **Company** | `id`, `name` (unique), `domain` (unique) |
| **Employee** | `id`, `name`, `email`, `password` (bcrypt), `role`, `skills[]`, `voice_print` (Vector 1024), `company_id` |
| **Project** | `id`, `name` (unique), `description`, `created_at`, `delivered`, `tags`, `company_id` |
| **Meeting** | `id`, `title`, `date`, `project_name`, `duration_sec`, `language`, `meta` (JSONB), `company_id` |
| **MeetingChunk** | `id`, `meeting_id`, `raw_text`, `summary_text`, `start/end_time_sec`, `embedding` (Vector **384**), `speaker_names[]` |
| **Note** | `id`, `project_name`, `author` (email), `note_text`, `embedding` (Vector **1024**), `date`, `type`, `tags`, `function`, `file_name`, `module`, `title`, `line_number`, `company_id` |
| **Task** | `id`, `project_name`, `assignee_name`, `description`, `status` (todo/in_progress/done), `source_type` (note/meeting), `company_id` |

Repositories in `core/database/repos.py` extend a generic `BaseRepository[T]`
(`create`, `get_by_id`, `update`, `delete`) with entity-specific queries (e.g.
`get_by_domain`, `get_by_email`, `get_all_by_project_name`).

---

## External Services

| Service | Used for | Details |
|---------|----------|---------|
| **Ollama** (local) | Embeddings + generation | `mxbai-embed-large` (1024-dim embeddings), `llama3.2` (generation); default `localhost:11434`. Configured in `core/rag/models.py` / `llm_config.py`; provider abstraction in `llm_factory.py` also supports OpenAI/Gemini |
| **PostgreSQL + pgvector** | Storage + similarity search | Port **5434** (docker compose). Uses `vector` (`<=>` cosine) and `pg_trgm` (fuzzy text) |
| **SMTP** | Sending OTP emails | Provider auto-selected by sender domain; credentials from `MIND_TRACE_EMAIL` / `MIND_TRACE_PASSWORD` |
| **HuggingFace / pyannote** | Speaker diarization | Requires `HF_TOKEN`; used by `SpeakerDiarizer` in the meeting pipeline |

---

## Build, Develop & Run

### Prerequisites
- **Python 3.13** (use a matching virtualenv/conda env).
- **Node.js** (project tested with Node 24) + npm.
- **Docker** (for the PostgreSQL + pgvector container).
- **Ollama** running locally with `mxbai-embed-large` and `llama3.2` pulled.

Install Python dependencies (Poetry, with a requirements fallback):
```bash
pip install poetry
poetry install
# or:
pip install -r requirements.txt
```

### Extension (repo root)
```bash
npm install
npm run compile     # one-time webpack build → dist/extension.js
npm run watch       # webpack watch mode (development)
npm run lint        # ESLint on src/
npm test            # extension tests (requires compile + lint first)
```

### Webview UI (`webview-ui/`)
```bash
npm install
npm run dev         # Vite dev server (browser preview only, not inside VS Code)
npm run build       # tsc + vite build → webview-ui/dist/ (extension loads from here)
npm run lint        # ESLint on webview-ui/src/
```
> The extension's `_buildHtml()` injects `webview-ui/dist/assets/index.js` + `index.css`,
> so **build the webview before launching the extension**.

### Backend (`backend/`)
```bash
# Start the API (from repo root or backend/)
python -m app.__main__              # uvicorn on 127.0.0.1:8000

# PostgreSQL (pgvector) container — port 5434
docker compose -f backend/docker/postgres/compose.yaml up -d

# Run migrations (note: migrations folder is named "almebic")
alembic -c backend/alembic.ini upgrade head
```

### Running the extension end-to-end
1. Start Postgres (docker) and Ollama.
2. Build the webview (`cd webview-ui && npm run build`).
3. Compile/watch the extension (`npm run watch`).
4. Start the backend (`python -m app.__main__`).
5. Press **F5** in VS Code to launch the Extension Development Host, then run
   **Mind-Trace: runextension** to open the sidebar.

### Regenerating the diagrams
The PNGs are rendered from the `.mmd` sources with the Mermaid CLI:
```bash
npx -y @mermaid-js/mermaid-cli -i diagrams/01_architecture_overview.mmd \
    -o diagrams/01_architecture_overview.png -t neutral -b white --scale 3
# …repeat for 02_main_user_flows, 03_note_and_rag_detail, 04_full_system_detail
```

---

## Environment Files

| File | Variables |
|------|-----------|
| `backend/.env` | `HF_TOKEN` (HuggingFace, pyannote diarization), `MIND_TRACE_EMAIL`, `MIND_TRACE_PASSWORD` (SMTP sender) |
| `backend/docker/postgres/postgres.env` | DB credentials + URL (loaded by `DatabaseConfigLoader`); Postgres on port 5434 |

---

## Known Issues

- **`backend/almebic/`** — folder name is a typo (should be `alembic`).
- **Embedding size mismatch** — `Note.embedding` and `Employee.voice_print` use 1024-dim,
  but `MeetingChunk.embedding` uses **384-dim** (`all-MiniLM-L6-v2`). Hybrid search mixes
  both spaces; keep this in mind when querying.
- **Search & AI Summary panels** historically shipped with mock data — verify they are
  wired to `/llms/search` and `/llms/send_query` before relying on them.
- **`app/notes/`** directory exists but is empty; note routing goes through `notes_apis.py`.
- **`Views/` vs `Panels/`** in `webview-ui` contain duplicate components (ongoing refactor).
- **`changeLLM`** message handler is a stub — selecting a model in the UI does not yet
  switch the backend model.
