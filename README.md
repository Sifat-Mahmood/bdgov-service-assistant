# Bangla Government-Service Assistant

A bilingual (Bangla + English) chat assistant that answers citizen questions
about four Bangladesh government services — **Passport, NID (National ID),
Tax (e-TIN / basic income tax), and Utility services** (electricity/gas/water
connection & billing). Every answer is grounded in real, collected
government documents via Retrieval-Augmented Generation (RAG), shows its
source, and the system honestly says **"I'm not sure"** instead of guessing
when it lacks confident coverage.

**🔗 Live app:** https://bdgov-service-assistant.vercel.app

**🔗 Live API:** https://bdgov-service-assistant.onrender.com

**🔗 API health check:** https://bdgov-service-assistant.onrender.com/health

---

## Table of Contents
- [Problem & Motivation](#problem--motivation)
- [Features](#features)
- [Scope](#scope)
- [System Architecture](#system-architecture)
- [Request Flow](#request-flow-per-question)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Setup — Local Development](#setup--local-development)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)
- [Evaluation](#evaluation)
- [Engineering Journey — Why the Architecture Changed](#engineering-journey--why-the-architecture-changed)
- [Known Limitations](#known-limitations)
- [Roadmap / Next Steps](#roadmap--next-steps)

---

## Problem & Motivation

Bangladeshi citizens seeking accurate information about passport, NID, tax,
and utility-service processes — eligibility, required documents, fees, and
processing times — have no single trustworthy, conversational source.
Existing information is fragmented across government sites, social media
groups, and outdated blog articles, causing wasted trips, incorrect
payments, and application delays.

**Target user:** Any citizen with a phone or browser trying to figure out
passport, NID, tax, or utility-service requirements before visiting an
office or making a payment.

**Success looks like:** a user asks a real question in Bangla or English and
gets a correct, cited answer — or an honest "I'm not sure, here's who to
contact" — every time.

## Features

- 🌐 **Bilingual Q&A** — ask in Bangla or English; the system detects the
  language and answers in kind (F9).
- 📚 **Grounded RAG across 4 domains** — every answer is generated only from
  retrieved passages of real government source documents, never from the
  model's outside knowledge (F2, F3).
- 🔖 **Source citations on every answer** — each response shows the
  document and excerpt it was grounded in (F4).
- ⚠️ **Honest confidence-based abstention** — when retrieval or the model
  itself signals low confidence, the system returns an "I'm not sure"
  response with a pointer to the correct official channel instead of
  guessing (F5).
- 🧭 **Domain routing** — automatically classifies each question into
  Passport / NID / Tax / Utilities, or flags it out-of-scope (F6).
- ❓ **Clarifying questions** — asks a follow-up when a question is
  ambiguous, e.g. "new passport or renewal?" (F7).
- ❤️‍🩹 **Health-check endpoint** for uptime monitoring (F11).

## Scope

**In scope (4 domains):**

| Domain | Covers |
|---|---|
| **Passport** | Eligibility, validity (5/10 yr), required documents, fees (incl. VAT), processing times (regular/express/super-express), delivery types |
| **NID** | New registration, correction, required documents for adults/minors |
| **Tax** | e-TIN registration, who needs to file, basic individual income-tax filing requirements, common deadlines |
| **Utilities** | New electricity/gas/water connection requirements, required documents, standard billing/complaint procedures |

**Explicitly out of scope** (the system will say so rather than guess):
land registration, trade licenses, visas, passports for foreign nationals,
real-time application status tracking, payment processing, voice
input/output, model fine-tuning, multi-turn negotiation beyond one
clarification round, a native mobile app, and Customs/VAT (a distinct tax
domain from the "basic individual income-tax" scope covered here).

**Not currently included** (see [Known Limitations](#known-limitations) and
[Engineering Journey](#engineering-journey--why-the-architecture-changed)):
user accounts, login, and persisted chat history — cut deliberately during
deployment to fit free-tier hosting memory limits.

---

## System Architecture

### As originally planned

```
                    ┌─────────────────────┐
                    │   React Frontend    │
                    │  (chat UI, auth)    │
                    └──────────┬──────────┘
                               │ REST (HTTPS)
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Backend   │
                    │  (auth, sessions,   │
                    │   orchestration)    │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼─────────────────┐
              ▼                ▼                  ▼
     ┌────────────────┐ ┌─────────────┐  ┌──────────────┐
     │  Postgres DB    │ │  Chroma      │  │  LLM API      │
     │ (users, chats,  │ │  Vector DB   │  │ (Groq/OpenAI) │
     │  eval logs)     │ │ (doc chunks) │  │               │
     └────────────────┘ └─────────────┘  └──────────────┘
```

### As actually deployed

```
                    ┌─────────────────────┐
                    │   React Frontend    │
                    │  (chat UI, no auth) │
                    │  live on Vercel     │
                    └──────────┬──────────┘
                               │ REST (HTTPS)
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Backend   │
                    │  (stateless,        │
                    │   orchestration)    │
                    │  live on Render     │
                    └──────────┬──────────┘
                               │
                    ┌────────────────────┐
                    ▼                    ▼
     ┌───────────────────────┐  ┌──────────────┐
     │  In-memory retriever    │  │  LLM API      │
     │  (fastembed/ONNX +      │  │  (Groq)       │
     │  plain JSON index,      │  │               │
     │  numpy L2 search;       │  │               │
     │  no external DB)        │  │               │
     └───────────────────────┘  └──────────────┘
```

Postgres, Chroma, and JWT auth were all removed during deployment to fit a
hard 512MB RAM limit on free-tier hosting — the app now connects to nothing
external except the Groq API. Full reasoning in
[Engineering Journey](#engineering-journey--why-the-architecture-changed).

## Request Flow (per question)

1. Frontend sends `{question, session_id, language?}` to `POST /chat`.
2. **Router step** — classifies the question into `passport` / `nid` /
   `tax` / `utilities` / `out_of_scope`, and detects/normalizes the
   question's language.
3. If ambiguous → the system returns a clarifying question and waits for
   the next turn.
4. If in-scope → the question is embedded (`fastembed`, ONNX) and compared
   via squared-L2 similarity search against the pre-built in-memory index
   (45 chunks total, drawn from official passport/NID/tax/utility source
   documents), returning the top-k passages with source metadata.
5. **Answer step** — an LLM (Groq, `llama-3.3-70b-versatile`) generates an
   answer using *only* the retrieved passages — the system prompt
   explicitly instructs it not to use outside knowledge — returning
   structured `{answer, citations: [{doc, excerpt}], not_sure}`. `not_sure`
   is the model's own self-check, avoiding a second LLM call for that
   purpose.
6. **Confidence gate** — combines the retrieval distance score against
   `DISTANCE_THRESHOLD = 0.45` with the `not_sure` flag. If either signals
   low confidence, the response is replaced with an honest abstention
   pointing to the correct official contact channel instead of the LLM's
   raw (possibly wrong) output.
7. The response — answer, citations, domain tag, and a confidence
   indicator — renders in the chat UI.

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React + Vite, plain JavaScript | `.jsx` files, no TypeScript |
| Styling | Plain CSS | Chosen over Tailwind for zero build-config overhead |
| Linter | ESLint | |
| Backend framework | FastAPI (`fastapi==0.115.6`, `uvicorn==0.34.0`) | Async support, auto Swagger docs |
| Orchestration | Direct Groq SDK calls (not LangChain/LangGraph) | JSON-mode classification/generation was sufficient without an orchestration framework |
| Embeddings | `fastembed` (ONNX Runtime) — quantized `Xenova/multilingual-e5-small` | Replaces `sentence-transformers`/PyTorch; verified to match original pipeline's distances to 4 decimal places |
| Vector search | Plain JSON index (`app/data/index.json`) + NumPy L2 linear search | Replaces Chroma; functionally equivalent at 45-chunk scale |
| LLM | Groq — `llama-3.3-70b-versatile` (`groq==0.13.0`) | Free tier; fast latency |
| Database | *(none)* | Removed entirely — see Engineering Journey |
| Auth | *(none)* | `/chat` is fully anonymous |
| CORS | FastAPI `CORSMiddleware` | Scoped to the Vite dev server + the production Vercel origin |
| Backend hosting | **Render** (free tier) | No persistent disk; 512MB RAM limit; sleeps after 15 min idle |
| Frontend hosting | **Vercel** (free tier) | |
| Version control | Git + GitHub | |

**Implementation details worth knowing:**
- `intfloat/multilingual-e5-small` (the base model family) requires text to
  be prefixed with `"passage: "` (at ingestion) or `"query: "` (at
  retrieval) per its training convention — implemented in both
  `ingestion/build_index.py` and `services/retriever.py`.
- `fastembed`'s `add_custom_model()` call requires `PoolingType.MEAN` and
  `normalization=True` to be specified explicitly (not auto-inferred the
  way `sentence-transformers` handled it).
- Both `router_agent.py` and `answer_agent.py` use Groq's
  `response_format={"type": "json_object"}` with `temperature=0` for
  reliable structured output.
- The plain-JSON retriever deliberately uses **squared L2 (Euclidean)
  distance**, matching Chroma's own default metric, so the existing
  `DISTANCE_THRESHOLD = 0.45` calibration remains valid without re-tuning.

---

## Project Structure

```
bdgov-service-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entrypoint; CORS config
│   │   ├── config.py                # env/settings loader (GROQ_API_KEY required)
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── chat.py              # POST /chat — anonymous, stateless
│   │   │   └── health.py            # GET /health
│   │   ├── services/
│   │   │   ├── router_agent.py      # domain classification + language detection
│   │   │   ├── retriever.py         # fastembed + JSON/numpy similarity search
│   │   │   ├── answer_agent.py      # grounded answer generation
│   │   │   └── confidence.py        # distance + not_sure confidence gate
│   │   ├── data/
│   │   │   └── index.json           # pre-built embedding index (45 chunks), committed
│   │   └── ingestion/
│   │       ├── build_index.py       # chunk + embed + write index.json (run once)
│   │       └── documents/           # raw source text files, organized by domain
│   │           ├── passport/
│   │           ├── nid/
│   │           ├── tax/
│   │           └── utilities/
│   │               └── gas/         # nested — gas is part of Utilities, not a separate domain
│   ├── eval/
│   │   ├── eval_questions.json      # scripted eval question bank
│   │   └── run_eval.py              # eval runner (planned)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # renders ChatWindow unconditionally (no auth gate)
│   │   ├── App.css
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx       # message list state, session_id, wiring
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── CitationChip.jsx     # expandable source excerpt
│   │   │   ├── ConfidenceBadge.jsx  # visually distinct confident/not-confident state
│   │   │   └── DomainTag.jsx        # small "Passport"/"Tax"/etc. indicator
│   │   ├── api/
│   │   │   └── client.js            # sendChatMessage (BASE_URL via VITE_API_URL)
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── docs/
    ├── proposal.md
    ├── final_report.md
    ├── PROJECT_REQUIREMENTS.md
    └── PROGRESS_LOG.md
```

Removed entirely during deployment (present in earlier plans, not in the
current repo): `models/db_models.py`, `routers/auth.py`,
`services/auth_service.py`, the whole `db/` folder, and `chroma_db/` — see
[Engineering Journey](#engineering-journey--why-the-architecture-changed).

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Liveness check |
| POST | `/chat` | None (always anonymous) | `{question, session_id, language?}` → `{answer, citations, confident, domain}` |

`/auth/register`, `/auth/login`, and `/chat/history` do not exist — auth and
persistence were removed entirely (see Engineering Journey). The optional
`language` field in a `/chat` request is currently accepted but not yet
wired into routing logic; the router's own auto-detected language drives
the actual response.

**Example request:**
```json
POST /chat
{
  "question": "What documents do I need for a new passport application?",
  "session_id": "a1b2c3d4-...",
  "language": null
}
```

**Example response:**
```json
{
  "answer": "You need... [grounded answer text]",
  "citations": [
    {"doc": "required_documents.txt", "excerpt": "..."}
  ],
  "confident": true,
  "domain": "passport"
}
```

---

## Setup — Local Development

### Prerequisites
- Python 3.12.10 (pinned to match the deployed environment)
- Node.js (for the Vite frontend)
- A Groq API key (free tier available at [console.groq.com](https://console.groq.com))

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# create backend/.env:
echo "GROQ_API_KEY=your_key_here" > .env

# the embedding index (app/data/index.json) is committed to the repo,
# so no ingestion run is required to start the server. To rebuild it
# from source documents:
python app/ingestion/build_index.py

uvicorn app.main:app --reload
# → http://127.0.0.1:8000, Swagger docs at /docs
```

### Frontend
```bash
cd frontend
npm install

# create frontend/.env.local:
echo "VITE_API_URL=http://127.0.0.1:8000" > .env.local

npm run dev
# → http://localhost:5173
```

Run both together for a full local end-to-end experience.

---

## Environment Variables

| Variable | Where | Required | Notes |
|---|---|---|---|
| `GROQ_API_KEY` | Backend (`.env`) | ✅ Yes — only required var | Fails loudly on startup if missing |
| `PYTHON_VERSION` | Render dashboard | Recommended | Pinned to `3.12.10` to match local dev |
| `VITE_API_URL` | Frontend (`.env.local` / Vercel dashboard) | ✅ Yes | Falls back to `http://127.0.0.1:8000` if unset |

`.env` and `.env.local` are both git-ignored — never commit real secrets.
No `DATABASE_URL` or `JWT_SECRET_KEY` are needed; both were removed along
with the database/auth layer.

---

## Deployment

| Component | Platform | Notes |
|---|---|---|
| Backend | [Render](https://render.com) (free tier) | No persistent disk — the embedding index is committed to the repo instead of generated at runtime. 512MB RAM limit. Sleeps after 15 minutes idle (cold-start latency not yet formally measured). |
| Frontend | [Vercel](https://vercel.com) (free tier) | Deployed with Root Directory scoped to `frontend/` specifically — the repo also contains a Python backend, which Vercel would otherwise try to auto-deploy as an incompatible serverless function. |

CORS on the backend (`allow_origins`) includes both the local Vite dev
server (`http://localhost:5173`) and the production Vercel origin.

---

## Evaluation

A six-case smoke test has been run and verified directly against the
**live, deployed** app (not localhost):

| Question | Domain | Result |
|---|---|---|
| "What documents do I need for a new passport application?" | Passport | ✅ Confident, 2 citations |
| "আমার এনআইডি সংশোধন করতে কী কী কাগজ লাগবে?" (Bangla) | NID | ✅ Confident, Bangla answer, 1 citation |
| "How do I register a land plot in my name?" | Out-of-scope | ✅ Correctly refused |
| "What is the deadline for filing income tax returns?" | Tax | ✅ Confident, 1 citation, correct date |
| "What documents do I need for a new electricity connection?" | Utilities | ✅ Confident, 3 citations |
| "How do I file a billing complaint for my electricity connection?" | Utilities | ✅ Correctly abstained (known documentation gap) |

An expanded scripted evaluation set (`eval/eval_questions.json`) targeting
30–40 questions across all four domains — including clarification and
abstention cases — is in progress; see that file's `status` field for which
questions have been executed vs. drafted only. Full details and a
per-domain breakdown are in `docs/final_report.md`.

---

## Engineering Journey — Why the Architecture Changed

The single biggest technical story in this project happened during
deployment, fitting the app inside Render free tier's **hard 512MB RAM
limit**. Three real production failures were diagnosed to root cause, two
full library swaps were made (each verified to preserve retrieval
correctness before being adopted), and one deliberate, explicitly-approved
scope cut was made — nothing was guessed or rushed.

### 1. Embeddings: `sentence-transformers` → `fastembed`
`sentence-transformers`/PyTorch's real, measured memory footprint —
**781.5MB**, even after switching to the CPU-only PyTorch build — made
free-tier deployment impossible, discovered via three consecutive deploy
failures (a port-scan timeout from module-level model loading, then two
separate out-of-memory kills). Replaced with `fastembed` (ONNX Runtime, no
PyTorch), loading a quantized ONNX export of the same base model
(`Xenova/multilingual-e5-small`) via `add_custom_model()`. **Verified
empirically:** a known-good test question produced identical retrieved
passages and distance scores (to 4 decimal places) versus the original
pipeline.

### 2. Vector DB: Chroma → plain JSON + NumPy
Even after the `fastembed` swap, `chromadb` alone cost **~49MB** just to
import — it unconditionally pulls in a Kubernetes client, `grpcio`, and a
full OpenTelemetry stack supporting a remote-server mode this project never
used. At the project's actual scale (45 chunks), a full vector database was
disproportionate machinery. Replaced with a plain JSON index + NumPy linear
search using squared L2 distance (Chroma's own default metric), so the
existing confidence threshold stayed valid without re-tuning. **Verified
empirically:** identical results to 4 decimal places. Measured savings:
~22MB.

### 3. Auth + database: removed entirely (not deferred)
After the two swaps above still left only a **~14MB** safety margin, and
after a full code review confirmed no further safe reduction was available,
removing Postgres persistence and JWT auth was proposed and **explicitly
approved by the user**. This was not an arbitrary cut — the project's own
priority ordering already ranked "a database and basic auth" as the
lowest-priority Must-requirement, below grounded RAG and agentic behavior.
Removed: `routers/auth.py`, `services/auth_service.py`, the entire `db/`
folder, `models/db_models.py`, all auth-related Pydantic schemas, and
`sqlalchemy`, `psycopg2-binary`, `greenlet`, `passlib[bcrypt]`, `bcrypt`,
`python-jose[cryptography]`, `email-validator`, `dnspython` from
`requirements.txt`. The frontend's `AuthForm.jsx` and related code were
removed to match.

**Measured result:** real full-app memory dropped from **498.7MB to
470.7MB** — a genuine **~41MB** safety margin under the 512MB ceiling,
versus the prior ~14MB knife-edge. `/chat` is now anonymous-only, with no
history persistence in any form.

Every one of these changes is logged, with its full reasoning, in
`docs/PROJECT_REQUIREMENTS.md`'s revision log and `docs/PROGRESS_LOG.md`
Section 15 — nothing here is undocumented or accidental.

---

## Known Limitations

- **Confidence-gate partial-credit bug (known, reproduced, not yet fixed):**
  a specific passport-fee question ("How much does a 10 year passport
  cost?") produced a correct, well-cited answer that was discarded because
  the model flagged `not_sure: true` over one partial, cut-off sub-detail.
  The current gate (`distance_ok AND NOT not_sure`) has no partial-credit
  handling. Confirmed isolated, not systemic. A fix requires data-driven
  tuning against the full eval set.
- **No persistence or authentication** — a deliberate, approved scope cut
  for hosting-memory reasons, not an oversight.
- **Vector search is linear, not indexed** — fine at the current 45-chunk
  scale; would need re-evaluation if the document collection grew
  significantly.
- **Source data quality issues, documented at collection time:**
  - Two conflicting passport document checklists were kept side-by-side
    rather than reconciled.
  - NID fee data is sourced from a 2015 notice; no more current official
    page was found.
  - Tax source content is a paraphrased FAQ summary, not verbatim text.
  - NID issuance authority transitioned from the Election Commission to
    the Home Ministry's NID Registration Wing; both eras of content coexist
    in the source material.
- **Groq free-tier daily token limit** (100,000 tokens/day) has been hit
  twice during development; a second API key is used as a practical
  mitigation.
- **Render free-tier cold-start latency** (sleeps after 15 min idle) has
  not been formally measured.
- The optional `language` field on `/chat` requests is accepted but not
  yet wired into routing logic.
- **F6a** (a single question spanning two domains) is deferred, not
  implemented.

## Roadmap / Next Steps

- Complete the expanded evaluation set (NID, Tax, Utilities questions) and
  execute the full run.
- Data-driven redesign of `confidence.py`'s gate to handle partial credit
  instead of an all-or-nothing `not_sure` override.
- Formally measure Render cold-start latency.
- Wire the `language` request field into routing, or remove the stub.
- Implement F6a (cross-domain single-question handling).
- If a paid tier or alternative host becomes available: reintroduce
  Postgres persistence and basic auth (F8), and admin/dev query-logging
  (F10).

---

## Credits

Built as a solo capstone project for an AI Engineering Bootcamp. Source
documents collected from official Bangladesh government portals:
`epassport.gov.bd`, `services.nidw.gov.bd` / `nidw.gov.bd`, and
`nbr.gov.bd`.
