# Smart Meet

Meeting intelligence app for the assignment: upload a labelled transcript, extract decisions / action items / risks, and ask questions that are answered only from that meeting.

I picked **Option 3**. The interesting part is not “chat with a document” — it is keeping answers grounded when people hedge, assign work, or change their mind mid-discussion.

Stack: **Next.js + FastAPI + Postgres/pgvector + Ollama** (`llama3.1` + `nomic-embed-text`). No cloud API key required for a local demo.

---

## a. Quick setup

You need: Python 3.12, Node 20+, Docker (for Postgres), [Ollama](https://ollama.com), and **ffmpeg** if you want voice-to-transcript.

```bash
# 1. Models (once)
ollama pull llama3.1
ollama pull nomic-embed-text

# 2. Database
cd backend
docker compose up -d postgres
cp .env.example .env

# 3. API
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload
# http://localhost:8000/docs

# 4. UI (new terminal)
cd frontend
npm install
npm run dev
# http://localhost:3000
```

Postgres is on **5433**, not 5432, so it does not fight a Homebrew/Postgres install. If Conda `(base)` is active, do not run bare `python` / `uvicorn` — they miss `asyncpg`. Use `.venv/bin/python`.

Transcripts are any `.txt` meeting file: labelled turns, chat exports, Zoom-style lines, or loose notes. Known layouts parse instantly. Everything else is read by `llama3.1` into speaker turns (samples: `backend/tests/fixtures/sample_meeting.txt`, `backend/tests/fixtures/project_discussion_chat.txt`).

```text
[00:00:12] Sarah:
We need to release the payments feature next Friday.

Sarah: John will own the API.
```

Speaker roles after an em dash are stripped (`Maya Patel — Project Manager` → Maya Patel). Times like `[9:30 AM]` become `09:30:00`. Missing times are filled in order.

Upload that from **New meeting**, or switch to **Voice** to record / attach audio (Whisper runs locally). Wait until status is ready, then ask “What decisions were made?”

Backend tests (no Ollama needed):

```bash
cd backend && .venv/bin/python -m pytest
```

---

## b. Architecture

```text
┌─────────────┐     ┌──────────────────────────────────────────────┐
│  Next.js    │     │  FastAPI                                     │
│  :3000      │────▶│                                              │
│             │     │  upload  → Whisper (audio) → parse → chunk   │
│  meetings,  │     │           → embed → pgvector                 │
│  transcript,│     │           → llama3.1 JSON analysis           │
│  insights,  │     │  chat    → rewrite follow-up                 │
│  RAG chat   │     │           → hybrid retrieve + rerank         │
│             │     │           → llama3.1 grounded answer         │
└─────────────┘     └──────────────┬───────────────────────────────┘
                                   │
                    ┌──────────────▼──────────┐     ┌─────────────┐
                    │  Postgres :5433         │     │  Ollama     │
                    │  meetings, segments,    │     │  :11434     │
                    │  insights, chunks+vecs  │     │  chat+embed │
                    └─────────────────────────┘     └─────────────┘
```

Ingestion is **synchronous** on `POST /api/v1/meetings`. Chat is `POST /api/v1/meetings/{id}/chat`. Retrieval is always scoped by `meeting_id`.

Layers on the API side: routes → services → repositories → SQLAlchemy models. I wanted the RAG path readable in a review without hunting through a framework graph.

---

## c. What it would take to productionize

This MVP is a laptop demo. To run it on a hyperscaler I would not start by adding more RAG features — I would stop doing expensive work on the request thread.

**Ingestion.** Embeddings + structured extraction should move to a worker. On AWS that is S3 (raw `.txt`) → SQS → ECS/Fargate worker → RDS. Same idea on GCP (Cloud Storage + Pub/Sub + Cloud Run) or Azure (Blob + Queue + Container Apps). Upload then returns `202` and the UI polls status, which the model already has (`uploaded` / `processing` / `ready` / `failed`).

**Data.** Keep Postgres + pgvector until it actually hurts. RDS / Cloud SQL / Azure Database with the vector extension is enough for meeting-scoped search. I would not introduce Pinecone or OpenSearch until we need cross-tenant scale or hybrid search the database cannot do.

**Models.** Swap Ollama for a managed endpoint (Bedrock, Vertex, Azure OpenAI). Same OpenAI-compatible client, different `base_url`. Embeddings and chat should be versioned so a model change does not silently mismatch `embedding_dimensions`.

**Auth and tenancy.** There is none today. Every meeting is visible to anyone who can hit the API. Production needs real auth (Cognito / Identity Platform / Entra) and `user_id` (or org) on every row, enforced in SQL the same way `meeting_id` is enforced now.

**Frontend.** Vercel, CloudFront + S3, or Cloudflare Pages. The API is a separate service. CORS and `NEXT_PUBLIC_API_URL` have to stop being localhost.

**Safety / scale.** Redis for rate limits (in-memory limiter dies with the process). Object size limits at the load balancer. Secrets Manager / GSM / Key Vault instead of `.env`. Health checks that actually ping Postgres and the model, not `{"status":"ok"}`.

**Observability.** Structured logs are already there. Add traces (OpenTelemetry) on ingest, retrieve, and complete. Sample prompts only behind a flag — `ENABLE_AI_TRACES` exists for a reason.

**Cloudflare-shaped version.** Pages for the UI, Workers for a thin BFF, Hyperdrive or Neon for Postgres, Queues + a container for embedding. I would only do that if the team already lives on Cloudflare; AWS/GCP is the more boring default.

I would not “Kubernetes it” for an app this size. One API service, one worker, one database.

---

## d. RAG / LLM approach and decisions

I treated this as a **meeting** problem, not a generic PDF chatbot. People say “we should”, “John will own”, “the risk is Stripe” — the system has to tell those apart and refuse to invent an owner when nobody named one.

| Piece | Considered | Shipped | Why |
|---|---|---|---|
| LLM | OpenAI GPT-4o-mini, hosted Llama, Ollama | **Ollama `llama3.1`** | Reviewer can run it without my API key. JSON mode is good enough. Quality is worse than GPT-4; I accepted that for a local MVP. |
| Embeddings | `text-embedding-3-small` (1536), Ollama `nomic-embed-text` (768) | **`nomic-embed-text`** | Same process as chat. One less vendor. Migration `0002` exists because I originally assumed 1536-d. |
| Vector DB | Pinecone, Chroma, pgvector | **pgvector** | Meetings already live in Postgres. Isolation is `WHERE meeting_id = …`, not a metadata filter I might forget. |
| Orchestration | LangChain, LlamaIndex, hand-rolled | **hand-rolled** | The pipeline is short. A framework would hide the part I wanted to show. |
| Retrieval | Dense-only, BM25-only, hybrid | **hybrid + RRF + lexical rerank** | Names, dates, and “action items” are lexical. Paraphrases are dense. Both miss alone. |

**Chunking.** Target ~500 tokens, max 600, ~80 overlap. Never split a speaker turn. Short transcripts stay one chunk so we do not over-fragment a 10-minute standup. Naive sliding windows on raw text were the first thing I rejected — they cut “John will own the API” in half.

**Prompts / context.** Prompt version `rag-v2`. Transcript goes in `<untrusted_transcript>` so the model is told not to obey instructions inside the meeting. Context is capped (~3500 tokens). Last 6 chat turns are included. Questions about decisions / actions / risks get the structured extraction **and** retrieved chunks, because “what did we decide?” should not depend on whether the vector search liked that paragraph.

**Follow-ups.** “Was it accepted?” is rewritten into a standalone question using history, with a dumb heuristic fallback if the rewrite call fails.

**Guardrails.** `.txt` or audio (wav/mp3/m4a/webm), size/UTF-8 checks, in-memory rate limits, citation IDs must be in the retrieved set, abstain if the best vector score is below `0.18`. The fallback copy is fixed: we did not find enough evidence. I would rather look cautious than confidently wrong.

**Quality.** Pytest on parser, chunking, retrieval scoping, citation filter, JSON parse, and a small eval *catalog* (direct fact, follow-up, missing info, prompt injection). That catalog checks routing, not answer quality. I did not put a live LLM eval in CI because it is slow, flaky, and needs Ollama on the runner.

**Observability.** JSON logs on retrieve/complete: meeting id, scores, chunk ids, latency, model names, prompt version. Not a tracing product.

---

## e. Key technical decisions

**One database.** Authorization and vectors in the same place. For this assignment that is a feature, not a limitation.

**Local models.** I wanted `git clone` + Ollama + Docker Postgres to be enough. Hosted models would look better in a screenshot and worse in a take-home.

**Sync ingest.** Wrong for production, right for a demo. You upload, you wait, you get a ready meeting. A queue would have been more “correct” and harder to run in 15 minutes.

**Custom UI, not shadcn.** I needed a small set of components and full control over the transcript/chat layout. `tech.md` still says shadcn from an earlier plan; I did not go back and install it.

**Parser then model.** Known layouts (`[HH:MM:SS] Name:`, chat-style `[9:30 AM] Name — Role`, `Name: …`) parse in code. Unknown `.txt` is converted to turns by `llama3.1`. That is slower and can mis-attribute a speaker; I still would not spend a weekend on Zoom/VTT archaeology for an MVP.

**No auth.** Out of scope for a local single-user demo. I still scoped retrieval by meeting so the RAG path is shaped like a multi-tenant query.

---

## f. Engineering standards I followed (and skipped)

**Followed**

- Typed Python 3.12, Pydantic on requests and model JSON
- SQLAlchemy 2 + Alembic (including the embedding-dimension migration)
- Layered backend so RAG is not stuffed into the route
- Structured logs and `X-Request-ID`
- Ruff config, pytest on the bits that are easy to get wrong (parser, chunks, guards)
- Next.js App Router + TypeScript, explicit error/empty/not-found states

**Skipped on purpose**

- GitHub Actions
- Frontend unit tests and Playwright
- OpenTelemetry
- Auth, async workers, streaming
- Putting the frontend in Docker Compose
- A real RAG eval harness

`tech.md` still lists some of those as if they shipped. They did not. I would rather say that here than leave a reviewer hunting for CI that does not exist.

---

## g. How I used AI tools

I used **Cursor** heavily: scaffolding FastAPI/Next, iterating on layout, and drafting boilerplate (forms, repositories, Docker). I did not use it as an autopilot for architecture.

What I actually did:

- Let it generate the first pass of CRUD and UI chrome, then I tightened RAG, chunking, and prompts until I could explain every step.
- When the UI got too tight or too loose, I asked for a spacing pass, then checked it in the browser myself.
- I kept tests on parser / chunking / guardrails as a check on generated code. If I cannot write a test for it, I do not understand it.

**Do**

- Use it for glue and for “make this layout less ugly”
- Re-read retrieval and prompts as if a stranger wrote them
- Keep model/DB choices in *your* notes, not whatever the assistant defaulted to

**Don’t**

- Paste a README you did not edit (this file is the exception I still rewrote)
- Accept LangChain-or-Pinecone because it showed up in a template
- Ship a `tech.md` full of tools you never added (I left that table as a warning to myself)

Repeatable bit: the interesting path is small (`parser → chunk → retrieve → prompt`). If an assistant changes that, I expect to see it in git and in a test.

---

## h. What I would do with more time

If I had another week, in this order:

1. **Queue ingest** so a long transcript cannot time out the upload.
2. **A tiny golden set** I actually score (decision vs suggestion, missing budget, injection). Even 15 questions would tell me if `llama3.1` is lying.
3. **Streaming chat** and persisting threads (refresh currently wipes the conversation).
4. **Auth** and per-user meetings.
5. **CI** (ruff + pytest + `next lint`) and a Compose `DATABASE_URL` that works inside Docker.
6. Zoom/VTT parsers, named-speaker diarization, cross-meeting search, OpenTelemetry.

**Edge cases I did not handle**

- Voice turns labelled `Speaker` (no named diarization)
- Zoom / Meet / VTT as first-class parsers (free-form `.txt` is read by the model when the layout is unknown)
- Overlapping speakers, `[inaudible]`, speaker `Unknown`
- Transcripts bigger than 5 MB / 400k chars
- Multi-user access control
- Model downtime beyond a 502
- Chat history on the server
- Docker-compose API talking to `localhost:5433` from inside the container (use `postgres:5432` there)

---

## Repo layout

```text
backend/app/api/v1/meetings.py      upload, list, detail, chat, delete
backend/app/services/               parse, chunk, embed, retrieve, RAG, guards
backend/app/llm/prompts.py
frontend/app/meetings/               UI
frontend/components/chat/            grounded Q&A + citations
```

`ASSIGNMENT_AUDIT.md` is my private checklist against the brief. `tech.md` is an early stack table and is **not** fully accurate — this README is.
