# Smart Meet Backend

FastAPI + PostgreSQL/pgvector backend for the Meeting Intelligence assignment.

## Local setup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

ollama pull llama3.1
ollama pull nomic-embed-text

docker compose up -d postgres
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload
```

The backend talks to a local Ollama server at `OLLAMA_BASE_URL` (default `http://localhost:11434/v1`). Chat and embedding models are selected with `CHAT_MODEL` and `EMBEDDING_MODEL`. No `OPENAI_API_KEY` is required. If the API runs in Docker, set `OLLAMA_BASE_URL=http://host.docker.internal:11434/v1`.

Voice uploads need **ffmpeg** on the PATH (`brew install ffmpeg` on macOS). The first transcription downloads the Whisper model (`WHISPER_MODEL`, default `base`). Use `tiny` if CPU is slow.

Postgres is published on **5433** so it does not collide with a local Homebrew/Postgres install on 5432. If Conda `(base)` is active, do not run bare `python` or `uvicorn` — those resolve to Conda and miss project packages such as `asyncpg`. Always use `.venv/bin/python`.

API docs:

```text
http://localhost:8000/docs
```

## Main API

- `GET /api/v1/health`
- `GET /api/v1/meetings`
- `POST /api/v1/meetings`
- `GET /api/v1/meetings/{meeting_id}`
- `DELETE /api/v1/meetings/{meeting_id}`
- `POST /api/v1/meetings/{meeting_id}/chat`

## Processing flow

1. Validate `.txt` transcript or audio (wav/mp3/m4a/webm)
2. Transcribe audio locally with Whisper, then parse timestamps and speakers.
   Known layouts (`[HH:MM:SS] Name:`, `[9:30 AM] Name — Role`, `Name: …`) parse in code.
   Anything else is converted to turns by the chat model.
3. Save transcript segments
4. Build speaker-aware chunks (400–600 tokens, overlap, never split a turn)
5. Embed chunks with the configured `EMBEDDING_MODEL`
6. Store vectors in pgvector
7. Extract structured summary, decisions, action items and risks
8. Mark meeting as ready

Questions use hybrid retrieval (vector + keyword), reranking, citation checks, and follow-up rewrite. If evidence is weak, the API abstains instead of guessing.

For the assignment MVP this processing is synchronous. In production it should move to a queue/worker architecture.
