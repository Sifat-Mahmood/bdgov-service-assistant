# PROJECT_REQUIREMENTS.md
## Bangladesh Government-Service Assistant (Bilingual RAG Agent)

**Status:** Single source of truth for this project — reflects the system as
actually designed and built. Timeline: 9 days, solo build.

---

## 1. Project Overview and Objectives

### 1.1 What we're building
A bilingual (Bangla + English) chat assistant that answers citizen questions
about four Bangladesh government services: **Passport, NID (National ID),
Tax (e-TIN / basic income tax), and Utility services** (electricity/gas/water
connection & billing). Answers are grounded in real government documents via
Retrieval-Augmented Generation (RAG), every answer shows its source, and the
system explicitly refuses to answer when it isn't confident rather than
guessing.

### 1.2 Why this problem
Citizens currently get this kind of information from scattered, inconsistent
sources (outdated blog posts, Facebook groups, word-of-mouth). Wrong
information about fees, required documents, or processing times causes real
wasted trips and money — and this holds across all four domains, not just
passport/NID. A grounded, citation-backed assistant is a genuine, solvable
slice of that problem, and covering four domains makes the product
meaningfully more useful as an everyday citizen tool rather than a narrow
demo.

### 1.3 Core objectives (in priority order)
1. Ship a **working, deployed** product — not a notebook, not a local demo.
2. Demonstrate real RAG (embeddings + vector search + citation) across
   multiple, distinct document domains.
3. Demonstrate agentic behavior: routing across four domains, clarification,
   and honest abstention.
4. Have a backend with a real database and basic auth — not just a
   stateless script.
5. Include a real evaluation set, sized to cover all four domains, proving
   the system's accuracy.
6. Document everything well enough that the report and video are quick to
   produce at the end.

### 1.4 Non-objectives
This is explicitly **not** trying to be an exhaustive government-services
platform. It covers four defined domains (Passport, NID, Tax, Utilities) and
it is fine — expected, even — to say "I don't handle that yet" for anything
outside them (e.g., land registration, trade licenses, visas).

---

## 2. Problem Statement

> Bangladeshi citizens seeking accurate, up-to-date information about
> passport, NID, tax, and utility-service processes — eligibility, required
> documents, fees, and processing times — have no single trustworthy,
> conversational source. Existing information is fragmented across
> government sites, social media, and outdated articles, leading to wasted
> trips, incorrect payments, and application delays.

**Target user:** Any citizen with a phone/browser trying to figure out
passport, NID, tax, or utility-service requirements before visiting an
office or making a payment.

**Success looks like:** A user asks a real question in Bangla or English and
gets a correct, cited answer — or an honest "I'm not sure, here's who to
contact" — every time.

---

## 3. Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| F1 | User can ask a question in a chat interface, in Bangla or English | Must | ✅ Done |
| F2 | System retrieves relevant passages from an index spanning all four domains (Passport, NID, Tax, Utilities) | Must | ✅ Done |
| F3 | System generates an answer grounded only in retrieved passages | Must | ✅ Done |
| F4 | Every answer displays its source document + excerpt | Must | ✅ Done |
| F5 | System detects low-confidence retrieval and returns an "I'm not sure" response with a fallback contact/pointer instead of guessing | Must | ✅ Done (known partial-credit edge case — see Section 15) |
| F6 | System routes queries to the correct domain (passport / NID / tax / utilities) or flags out-of-scope questions | Must | ✅ Done |
| F6a | System correctly handles single questions that span two domains (e.g., "what ID do I need for both my NID correction and passport renewal?") by retrieving from multiple domains in one turn | Should | Deferred |
| F7 | System asks a clarifying question when the query is ambiguous (e.g., "new passport or renewal?") | Should | ✅ Done |
| F8 | User can create an account (email/password) and see their past questions | Should | Dropped — see Section 6 for reasoning |
| F9 | System responds in the same language the question was asked in | Should | ✅ Done |
| F10 | Admin/dev can view logged queries, confidence scores, and sources used, for evaluation purposes | Should | Partial — confidence scores/sources available per-response via `/chat`, not queryable/aggregatable after the fact (no database) |
| F11 | Health-check endpoint for the deployed API | Must | ✅ Done |

## 4. Non-Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| N1 | Deployed and publicly accessible via a URL (no local-only demo) | ✅ Done |
| N2 | Response latency under ~8 seconds for a typical query | ✅ Verified |
| N3 | No hallucinated fees/document lists — every factual claim must be traceable to a retrieved passage | ✅ Enforced via system prompt + confidence gate |
| N4 | Codebase organized, committed incrementally to Git with meaningful messages | ✅ Ongoing |
| N5 | Secrets (.env) never committed | ✅ Verified |
| N6 | Basic error handling: malformed input, empty retrieval, LLM API failure all degrade gracefully (no raw stack traces to the user) | ✅ Verified (including a real live 429 rate-limit case) |
| N7 | System usable on both desktop and mobile browser widths | ✅ Done |

---

## 5. Features and Scope

### 5.1 In scope — four domains

| Domain | Covers |
|---|---|
| **Passport** | Eligibility, validity (5/10 yr), required documents, fees (incl. VAT), processing times (regular/express), delivery types |
| **NID** | New registration, correction, required documents for adults/minors |
| **Tax** | e-TIN registration, who needs to file, basic individual income-tax filing requirements, common deadlines |
| **Utilities** | New electricity/gas/water connection requirements, required documents, standard billing/complaint procedures |

Plus, across all four domains:
- Bilingual Q&A (Bangla + English)
- Source citation on every grounded answer
- Confidence-based abstention
- A curated evaluation set (sized per Section 14) with pass/fail results in
  the report

### 5.2 Out of scope (explicitly — say so if asked, don't attempt)
- Any government service category beyond the four listed above (e.g., land
  registration, trade licenses, visas, passports for foreign nationals)
- Real-time application status tracking (would need live government API
  access — not available)
- Payment processing
- Voice input/output
- Fine-tuning any model
- Multi-turn complex negotiation dialogues beyond one clarification round
- Mobile native app (responsive web only)
- Customs and VAT (within Tax — a distinct domain from the "basic
  individual income-tax" scope defined above)
- User accounts, login, and persisted chat history (see Section 6)

### 5.3 Stretch goals (only if ahead of schedule)
- A fifth domain (e.g., trade license or land registration FAQs)
- Streaming responses (token-by-token) in the chat UI
- Admin dashboard showing query volume, top questions, low-confidence rate,
  and per-domain breakdown

---

## 6. System Architecture

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

**Why no database or auth:** Render's free tier enforces a hard 512MB RAM
ceiling. To fit within it, the originally-planned Postgres persistence and
JWT auth layer was removed entirely, not deferred. This is a deliberate,
approved trade-off consistent with Section 1.3's own priority ordering,
which ranks "a real database and basic auth" (priority #4) below grounded
RAG (#2) and agentic behavior (#3). `/chat` is fully anonymous and
stateless; F1–F7, F9, and F11 remain completely intact. Real, measured
full-app memory: **470.7MB**, a genuine ~41MB margin under the 512MB limit.

### 6.1 Request flow (per question)
1. Frontend sends `{question, session_id, language?}` to `/chat`.
2. Backend's **Router step** classifies domain (passport / NID / tax /
   utilities / out-of-scope) and detects/normalizes language.
3. If ambiguous → return a clarifying question, wait for the next user turn.
4. If in-scope → embed the question, run similarity search against the
   in-memory index, retrieve top-k passages with metadata (source doc,
   excerpt).
5. **Answer step:** the LLM generates an answer using *only* the retrieved
   passages, explicitly instructed not to use outside knowledge, and
   returns a `not_sure` self-check flag alongside structured citations.
6. **Confidence gate:** combines the retrieval distance score against a
   threshold with the `not_sure` flag. If either signals low confidence,
   the response is replaced with an honest abstention pointing to the
   correct official contact channel.
7. Response (answer, citations, domain, confidence) returns to the frontend
   and renders with a domain tag and confidence badge.

---

## 7. Technology Stack and Rationale

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite, plain JavaScript (not TypeScript) | Fast to build; `.jsx` files |
| Styling | Plain CSS | Zero build-config overhead; speed over polish given the timeline. Built on top of the Vite scaffold's existing CSS custom-property/dark-mode system |
| Linter | ESLint | Long-established, better-documented standard |
| CORS | FastAPI `CORSMiddleware` | Required for the React frontend to call the FastAPI backend from the browser; `allow_origins` includes both the local Vite dev server and the production Vercel origin |
| Backend | FastAPI (Python), `fastapi==0.115.6` / `uvicorn==0.34.0` | Async support fits LLM/network calls well; auto docs via Swagger help demo/grading |
| Orchestration | Direct Groq SDK calls (not LangChain/LangGraph) | The direct approach was sufficient for the JSON-mode classification/generation pattern needed; simpler and faster to build reliably across four domains |
| Vector search | Plain JSON file (`app/data/index.json`) + `numpy`-based linear L2 search, no external vector DB library | At this project's scale (45 chunks), a full vector database is disproportionate machinery. Zero external infra; functionally equivalent to a proper vector DB at this scale, verified via identical retrieval results against a Chroma-based baseline |
| Embeddings | `fastembed` (ONNX Runtime backend, no PyTorch), using a quantized ONNX export of `intfloat/multilingual-e5-small` (`Xenova/multilingual-e5-small`) | Multilingual (Bangla + English) support at a fraction of PyTorch's memory footprint — critical for fitting free-tier hosting's 512MB RAM limit. Verified empirically to produce identical retrieval results (same distances, same top passages, to four decimal places) versus a `sentence-transformers`-based baseline |
| LLM | Groq (Llama 3.3 70B, `llama-3.3-70b-versatile`), `groq==0.13.0` | Free tier; fast latency, which matters since four domains mean more router + retrieval + generation calls overall |
| Database | None | Removed to fit the 512MB hosting memory limit — see Section 6 |
| Auth | None | `/chat` is anonymous-only, no accounts, no login — removed alongside the database |
| Backend hosting | **Render** (free tier) | No card required, straightforward FastAPI deploy. Live at `https://bdgov-service-assistant.onrender.com`. 512MB RAM limit, no persistent disk, sleeps after 15 minutes idle |
| Frontend hosting | **Vercel** (free tier) | Free, trivial React/Vite deploy. Live at `https://bdgov-service-assistant.vercel.app`. Deployed with Root Directory scoped specifically to `frontend/`, since the monorepo also contains an incompatible Python backend |
| Version control | Git + GitHub | Required by rubric |

**Implementation note (embeddings):** The `intfloat/multilingual-e5-small`
model family requires text to be prefixed with `"passage: "` (document-side,
at ingestion) or `"query: "` (question-side, at retrieval) per the model's
training convention. This is not optional — omitting it measurably degrades
retrieval quality. Implemented in both `ingestion/build_index.py` and
`services/retriever.py`. `fastembed`'s `add_custom_model()` call requires
`PoolingType.MEAN` and `normalization=True` to be specified explicitly (not
inferred automatically the way `sentence-transformers` handles it).

**Implementation note (Groq JSON mode):** both `services/router_agent.py`
and `services/answer_agent.py` use Groq's
`response_format={"type": "json_object"}` mode with `temperature=0`, so
structured output is returned directly rather than parsed out of free text.

**Implementation note (vector search):** the retriever deliberately uses
squared L2 (Euclidean) distance, matching Chroma's default metric, so
`confidence.py`'s calibrated `DISTANCE_THRESHOLD` remains meaningful
regardless of which retrieval backend is used underneath.

---

## 8. Folder / Project Structure

```
bdgov-service-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entrypoint; CORS config
│   │   ├── config.py               # env/settings loader; only GROQ_API_KEY required
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── chat.py             # /chat endpoint — anonymous, stateless
│   │   │   └── health.py           # /health
│   │   ├── services/
│   │   │   ├── router_agent.py     # domain classification + language detection
│   │   │   ├── retriever.py        # fastembed embeddings + JSON/numpy similarity search
│   │   │   ├── answer_agent.py     # grounded answer generation
│   │   │   └── confidence.py       # distance + not_sure confidence gate
│   │   ├── data/
│   │   │   └── index.json          # pre-built embedding index (45 chunks), committed to the repo
│   │   └── ingestion/
│   │       ├── build_index.py      # chunk + embed + write index.json (run once)
│   │       ├── test_pipeline.py    # scratch: single-file chunk/embed validation
│   │       ├── test_retrieval.py   # scratch: query/retrieval validation
│   │       └── documents/          # raw source text files, organized by domain
│   │           ├── passport/
│   │           ├── nid/
│   │           ├── tax/
│   │           └── utilities/
│   │               └── gas/        # nested — gas is part of Utilities, not a separate domain
│   ├── eval/
│   │   ├── eval_questions.json     # scripted eval question bank
│   │   └── run_eval.py             # scripted eval runner
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # renders ChatWindow unconditionally (no auth gate)
│   │   ├── App.css                 # full styling pass, built on index.css's CSS variables
│   │   ├── index.css               # Vite scaffold output (CSS variables, light/dark mode)
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx      # message list state, input, session_id, wires everything together
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── CitationChip.jsx    # expandable source excerpt
│   │   │   ├── ConfidenceBadge.jsx # visually distinct per confident/not-confident state
│   │   │   └── DomainTag.jsx       # small "Passport"/"Tax"/etc. indicator on every answer
│   │   ├── api/
│   │   │   └── client.js           # sendChatMessage; BASE_URL via VITE_API_URL env var
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── docs/
    ├── proposal.md
    ├── final_report.md
    └── PROJECT_REQUIREMENTS.md     # this file
```

---

## 9. Day-by-Day Roadmap

### Day 1–2 — Data Collection & Environment Setup
- [x] Collect and clean source documents for all four domains from official
  portals (`epassport.gov.bd`, `services.nidw.gov.bd`/`nidw.gov.bd`,
  `nbr.gov.bd`)
- [x] Set up local Python environment, chunking strategy (300–500 tokens)
- [x] Manual retrieval spot-checks (~5 questions per domain)
- **End-of-day checkpoint:** ✅ documents collected, chunked, retrieval
  spot-checked as relevant

### Day 3 — Agent Logic Core
- [x] Build router agent (domain classification + language detection)
- [x] Build answer agent (grounded generation with citations + `not_sure`
  self-check)
- [x] Build confidence logic (distance threshold + self-check combination)
- [x] Router accuracy pass against a deliberately tricky question set
- **End-of-day checkpoint:** ✅ router → retriever → answer pipeline works
  end-to-end for all four domains, bilingual

### Day 4 — Backend Core
- [x] FastAPI skeleton: `main.py`, `/health`, `/chat`
- [x] `/chat` verified across all four domains, clarification, out-of-scope,
  and empty-input cases via Swagger
- [x] Graceful error handling verified against a real live rate-limit error
- **End-of-day checkpoint:** ✅ `/chat` works end-to-end via Swagger

### Day 5 — Frontend
- [x] React (Vite) frontend: chat UI, message bubbles, citation chips
  (expandable), confidence badge, domain tag
- [x] Wired to the local backend with CORS configured
- [x] Full user journey verified in-browser across all four domains + one
  out-of-scope + one honest-abstention case
- **End-of-day checkpoint:** ✅ full chat experience works locally in the
  browser

### Day 6 — Deployment
- [x] Backend deployed to Render, frontend deployed to Vercel
- [x] Both live and publicly reachable
- [x] Full six-case smoke test run directly against the live URLs (all four
  domains, one out-of-scope, one abstention) — all six correct
- [x] CORS updated for the production frontend origin
- **End-of-day checkpoint:** ✅ a live public URL works across all four
  domains

### Day 7 — Evaluation + Polish
- [x] Draft an expanded evaluation set covering all four domains (in
  progress — Passport subset complete, other domains pending)
- [ ] Tune the confidence threshold against full eval results (a known
  partial-credit edge case is flagged — see Section 15)
- [ ] Fix bugs surfaced by eval
- [ ] Polish UI rough edges, empty/error states
- **End-of-day checkpoint:** eval results recorded and threshold tuned;
  live app handles edge cases gracefully

### Day 8 — Documentation + Submission
- [ ] Write `proposal.md`
- [ ] Write `final_report.md`: problem, design decisions, AI workflow, eval
  results, conclusions
- [ ] Finalize `README.md`: setup instructions, architecture summary,
  screenshots
- [ ] Take clean screenshots of the working app (one per domain, plus one
  abstention example)
- [ ] Record 3–5 min walkthrough video
- [ ] Final commit pass — clean history, no secrets committed
- [ ] Submit: repo link, live URL, video link, proposal, report

---

## 10. Detailed Implementation Plan Per Module

### 10.1 Ingestion Pipeline (`ingestion/build_index.py`)
Chunks source documents (300–500 tokens per chunk), embeds each chunk via
`fastembed`, and writes the result — embeddings, text, and metadata (source
doc, domain, language) — to `app/data/index.json`. Run once; the resulting
index is committed to the repo since Render's free tier has no persistent
disk to regenerate it at runtime.

### 10.2 Router Agent (`services/router_agent.py`)
Classifies each incoming question into one of `passport` / `nid` / `tax` /
`utilities` / `out_of_scope`, and detects/normalizes the question's
language. Output is a single `domain` field. F6a (a single question
spanning two domains) is explicitly out of scope for the router's current
design.

### 10.3 Retriever (`services/retriever.py`)
Loads `index.json` into memory once at startup. Embeds the incoming
question (with the `"query: "` prefix), computes squared L2 distance
against every chunk in the relevant domain, and returns the top-k closest
passages with their source metadata.

### 10.4 Answer Agent (`services/answer_agent.py`)
- Input: question, retrieved passages, language
- Output: answer text + list of citations used, plus a `not_sure: bool`
  self-check flag
- System prompt explicitly states: *"Answer only using the provided
  passages. If the passages do not contain enough information, say you are
  not sure — do not use outside knowledge."*
- Output parsed into structured `{answer, citations: [{doc, excerpt}],
  not_sure}`

### 10.5 Confidence Logic (`services/confidence.py`)
Combines two signals: (a) top retrieval distance vs.
`DISTANCE_THRESHOLD = 0.45` (calibrated from observed good-match distances
in the 0.22–0.37 range) OR (b) the answer agent's own `not_sure` flag → if
either fires, mark `confident: false`. When not confident, the response
includes a fallback message pointing to the official contact channel
instead of the LLM's raw output.

### 10.6 Frontend Chat Flow
- `ChatWindow` holds message list state (in React memory only, no
  `localStorage`), generates a per-mount `session_id` via
  `crypto.randomUUID()`, and calls `api/client.js` → `/chat`
- `CitationChip` renders expandable source excerpts
- `ConfidenceBadge` shows a visually distinct treatment when
  `confident: false`
- `DomainTag` shows a small domain indicator on every answer

---

## 11. API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Liveness check |
| POST | `/chat` | None (always anonymous) | `{question, session_id, language?}` → `{answer, citations, confident, domain}` |

The optional `language` field in a `/chat` request is currently accepted
but not yet wired into routing logic — the router's own auto-detected
language is what drives the answer.

---

## 12. Data Model

There is no database in the deployed system. The only persisted data is the
static embedding index (`app/data/index.json`), committed to the repo,
containing per-chunk: `id`, `domain`, `language`, `source_doc`, `text`, and
`embedding`.

---

## 13. Deployment

| Component | Host | Notes |
|---|---|---|
| Backend | **Render** (free tier) | Live at `https://bdgov-service-assistant.onrender.com`. No Chroma, no Postgres connection — the app connects to nothing external except Groq's API. Free tier: 512MB RAM, no persistent disk, sleeps after 15 minutes idle |
| Frontend | **Vercel** (free tier) | Live at `https://bdgov-service-assistant.vercel.app`. Deployed with Root Directory scoped to `frontend/` |

Python version pinned to `3.12.10` via a Render environment variable to
match the local development environment. CORS `allow_origins` includes both
the local Vite dev server and the production Vercel origin.

---

## 14. Testing and Validation Plan

1. **Manual retrieval spot-checks** (Days 1–2): confirm top-k passages are
   actually relevant for ~5 hand-picked questions per domain (20 total).
2. **Router accuracy pass** (Day 3): a deliberately tricky set of ~10
   questions designed to confuse domain classification (e.g., overlapping
   document requirements between NID and passport), checked for correct
   routing or appropriate clarification.
3. **Scripted evaluation set**: 30–40 question/answer pairs, roughly evenly
   spread across domains, covering:
   - ~6–8 clear questions per domain (fees, eligibility, documents,
     processing times)
   - At least 4 questions that should trigger the clarification flow
   - At least 4 questions that should trigger honest abstention
     (out-of-scope or genuinely unanswerable from the docs)
   - At least 4 Bangla-language questions, spread across domains
   - Recorded pass/fail + notes in `eval/eval_questions.json`, summarized
     with a per-domain breakdown in the final report
4. **Manual QA pass on the deployed app:** questions in both languages
   across all four domains, citations rendering correctly, plus one
   out-of-scope case and one honest-abstention case.
5. **Error-path checks:** empty question, extremely long input, LLM API
   timeout — confirm graceful failure, not a raw 500 to the user.

---

## 15. Assumptions, Constraints, and Risks

### Assumptions
- Official passport/NID/tax/utility FAQ and fee documents are findable and
  collectible from official government portals.
- A 512MB-RAM free hosting tier is workable for this project's actual scale
  (45 document chunks) with the right technology choices.
- Groq's free tier provides sufficient throughput for development and demo
  purposes, with awareness of its daily token limit.

### Constraints
- No budget for paid API usage (embeddings, LLM, hosting, database) — every
  component must run on a genuinely free tier.
- Solo build, extended but still tight timeline.
- Free-tier hosting (Render) enforces a hard 512MB RAM ceiling with no
  persistent disk.

### Known Risks

| Risk | Mitigation | Status |
|---|---|---|
| Free-tier hosting cold-starts or sleeps, hurting demo reliability | Ping the deployed backend before recording the video; mention this limitation in the report if it persists | Render's free tier confirmed to sleep after 15 minutes idle. Actual cold-start latency not yet formally measured |
| Confidence thresholding is unreliable (false confident / false abstain), and may need per-domain tuning if document quality varies by domain | Tune threshold empirically against the full eval set; consider a per-domain threshold if one domain's documents are noisier | A known, reproduced edge case exists: a correct, well-cited passport-fee answer was discarded because the model flagged `not_sure: true` over one partial, cut-off detail — the current gate (`distance_ok AND NOT not_sure`) has no partial-credit handling. Confirmed isolated via a follow-up test with a different, cleaner question. Flagged for data-driven tuning against the full eval set |
| Scope creep (adding a 5th domain, streaming UI, etc.) | Stretch goals only, attempted only if ahead of schedule | Holding — Tax scope was actively trimmed rather than expanded during data collection; F6a was explicitly deferred rather than implemented ahead of schedule |
| Groq free-tier daily token limit reached during testing | A second Groq API key is available as a practical mitigation; space out large test batches | Materialized twice during development, both times diagnosed via a real `429`/`rate_limit_exceeded` response and resolved by switching keys. No permanent fix beyond awareness + the backup key |
| Free-tier hosting's ~512MB RAM ceiling is incompatible with a PyTorch-based embeddings/vector-DB/database stack | Use lightweight, memory-efficient alternatives (ONNX-based embeddings, in-memory retrieval, no external database) chosen and verified for correctness before adoption | Resolved. Final measured footprint: 470.7MB, a genuine ~41MB margin under 512MB. Deployed and verified live |
| Source data quality gaps (conflicting documents, outdated fee notices, paraphrased content) | Flag known gaps explicitly in source-file headers and in the final report's limitations section rather than silently working around them | Documented: two conflicting passport document checklists kept side-by-side; NID fee data from a 2015 notice; Tax content is a paraphrased FAQ summary; NID issuance authority transition (Election Commission → Home Ministry) noted |

---

## 16. Deliverables and Submission Checklist

- [ ] **Project Proposal** (`docs/proposal.md`, 1–2 pages): problem
  statement, proposed solution, AI approach, tech stack
- [ ] **Code repository**: complete frontend + backend + ingestion code,
  clean commit history, no secrets committed
- [ ] **README.md**: setup instructions, architecture summary, description
  of AI model(s)/methodology, usage instructions, screenshots
- [x] **Deployed application**: live, publicly accessible URL, verified
  working end-to-end. Backend: `https://bdgov-service-assistant.onrender.com`.
  Frontend: `https://bdgov-service-assistant.vercel.app`. Verified via a
  full six-case smoke test (all four domains, one out-of-scope, one
  abstention) run directly against the live URLs.
- [ ] **Final Report** (`docs/final_report.md`, 3–5 pages): problem solved,
  design decisions, AI workflow, evaluation results, conclusions and
  limitations
- [ ] **Evaluation results**: `eval/eval_questions.json` + summarized
  pass/fail table in the report
- [ ] **3–5 minute walkthrough video**: problem → approach → live demo
  (including at least one citation example and one honest-abstention
  example)
- [ ] Video posted to LinkedIn, repo pinned on GitHub
- [ ] Final check: every checkbox in Sections 9 (roadmap) and this section
  is complete before submission

---

*This document is the single source of truth for the project.*
