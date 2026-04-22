# Retail Award RAG System Design
## MA000004 — Australian Fair Work Compliance Engine

---

## 1. Overview

Build a RAG (Retrieval-Augmented Generation) pipeline that ingests the General Retail Industry Award [MA000004], chunks and embeds it, then answers payroll-specific queries such as:

> *"What's the rate for a 16-year-old working Saturday 8am–2pm?"*

The system sits alongside your existing Next.js + Python + PostgreSQL todo-scaffold and becomes the foundation of your payroll compliance SaaS.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend                         │
│   Upload Award PDF  │  Chat UI  │  Rate Calculator Widget       │
└──────────┬──────────┴─────┬─────┴──────────────┬───────────────┘
           │                │                     │
           ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI (Python)                           │
│                                                                 │
│  /api/ingest   →  Ingestion Pipeline                            │
│  /api/chat     →  RAG Query Pipeline                            │
│  /api/rate     →  Structured Rate Calculator                    │
└──────────┬──────────────────────────┬───────────────────────────┘
           │                          │
     ┌─────▼──────┐           ┌───────▼────────┐
     │  pgvector  │           │   PostgreSQL    │
     │ (embeddings│           │  (structured    │
     │  + chunks) │           │   rate tables)  │
     └─────┬──────┘           └───────┬─────────┘
           │                          │
           └──────────┬───────────────┘
                      ▼
              ┌───────────────┐
              │  OpenAI API   │
              │  (embeddings  │
              │  + chat)      │
              └───────────────┘
```

---

## 3. Component Breakdown

### 3.1 Ingestion Pipeline (`/api/ingest`)

```
PDF (MA000004)
    │
    ▼
[1] PDF Parser          → extract raw text (PyMuPDF / pdfplumber)
    │
    ▼
[2] Pre-processor       → clean whitespace, fix ligatures, detect sections
    │
    ▼
[3] Semantic Chunker    → split by clause/schedule boundaries (~500 tokens)
    │                     e.g. "Schedule B — Junior Rates" stays intact
    ▼
[4] Metadata Extractor  → tag each chunk:
    │                     { section, clause, schedule, rate_type, age_group }
    ▼
[5] Embedding Model     → text-embedding-3-small (OpenAI) or local BGE-M3
    │
    ▼
[6] pgvector store      → INSERT chunks + embeddings + metadata
    │
    ▼
[7] Structured Parser   → extract rate tables → PostgreSQL rate_table
```

**Key insight**: Award documents have structured tables (Junior Rates, Penalty Rates, Allowances). Parse these into a **relational rate table** in addition to vector chunks. Use the rate table for precise arithmetic, use RAG for context/explanation.

### 3.2 RAG Query Pipeline (`/api/chat`)

```
User Query: "16yo Saturday 8am–2pm retail rate?"
    │
    ▼
[1] Query Classifier    → detect: age=16, day=Saturday, time=08:00-14:00
    │                     type: junior_penalty_rate
    ▼
[2] Query Rewriter      → expand to canonical form for better retrieval
    │
    ▼
[3] Hybrid Retrieval
    │   ├── Vector search  (pgvector cosine similarity, top-k=8)
    │   └── Keyword search (PostgreSQL FTS on chunk text)
    │       → RRF (Reciprocal Rank Fusion) to merge results
    ▼
[4] Rate Table Lookup   → direct SQL for calculable facts
    │                     SELECT rate FROM award_rates WHERE age=16
    │                     AND day_type='saturday' AND classification='retail'
    ▼
[5] Context Assembly    → combine retrieved chunks + rate table result
    │
    ▼
[6] LLM Generation      → GPT-4o with system prompt:
    │                     "You are an Australian Fair Work compliance assistant.
    │                      Use ONLY the provided Award context. Cite clause numbers."
    ▼
[7] Response + Citations → answer + source clause references + calculated total
```

### 3.3 Structured Rate Calculator (`/api/rate`)

Deterministic, no LLM needed for pure calculations:

```
Input:  { employee_age, employment_type, date, start_time, end_time, classification }
Output: { base_rate, penalty_multiplier, total_rate, hours, total_pay, applicable_clauses }

Logic:
  1. Determine junior rate % from age (Schedule B)
  2. Determine day type (weekday / Saturday / Sunday / PH)
  3. Look up penalty rate for day type + employment_type
  4. Apply: base × junior% × penalty_multiplier
  5. Check overtime thresholds
  6. Return breakdown with clause citations
```

---

## 4. Database Schema

```sql
-- Vector store for RAG
CREATE TABLE award_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    award_id    TEXT NOT NULL,           -- 'MA000004'
    chunk_text  TEXT NOT NULL,
    embedding   vector(1536),            -- pgvector
    section     TEXT,                    -- e.g. 'Schedule B'
    clause      TEXT,                    -- e.g. '18.1'
    page_num    INT,
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON award_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON award_chunks USING gin(to_tsvector('english', chunk_text));

-- Structured rate table (parsed from award tables)
CREATE TABLE award_rates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    award_id        TEXT NOT NULL,
    classification  TEXT NOT NULL,       -- 'retail_employee_level_1'
    employment_type TEXT NOT NULL,       -- 'full_time','part_time','casual'
    age_min         INT,                 -- NULL = adult rate
    age_max         INT,
    age_pct         NUMERIC(5,2),        -- e.g. 70.00 for 70% of adult
    day_type        TEXT NOT NULL,       -- 'weekday','saturday','sunday','public_holiday'
    time_from       TIME,                -- NULL = all day
    time_to         TIME,
    rate_multiplier NUMERIC(5,4),        -- e.g. 1.2500
    allowance_type  TEXT,                -- NULL for base rates
    clause_ref      TEXT,                -- e.g. 'cl.18, Schedule B'
    effective_date  DATE NOT NULL
);

-- Ingestion audit
CREATE TABLE award_ingestions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    award_id    TEXT,
    filename    TEXT,
    chunk_count INT,
    status      TEXT,
    ingested_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 5. Project File Structure

```
project-root/
├── frontend/                          # Next.js
│   ├── app/
│   │   ├── page.tsx                   # Home / dashboard
│   │   ├── chat/
│   │   │   └── page.tsx               # Chat UI with award Q&A
│   │   ├── calculator/
│   │   │   └── page.tsx               # Rate calculator widget
│   │   └── admin/
│   │       └── page.tsx               # Award upload + ingestion status
│   ├── components/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── RateCalculator.tsx
│   │   └── AwardUploader.tsx
│   └── lib/
│       └── api.ts                     # API client
│
├── backend/                           # FastAPI (Python)
│   ├── main.py                        # FastAPI app entry
│   ├── api/
│   │   ├── ingest.py                  # POST /api/ingest
│   │   ├── chat.py                    # POST /api/chat
│   │   └── rate.py                    # POST /api/rate
│   ├── services/
│   │   ├── pdf_parser.py              # PDF → raw text
│   │   ├── chunker.py                 # Semantic chunking
│   │   ├── embedder.py                # OpenAI embeddings
│   │   ├── rate_extractor.py          # Table → structured rates
│   │   ├── retriever.py               # Hybrid search (vector + FTS)
│   │   └── llm.py                     # LLM generation + prompts
│   ├── models/
│   │   ├── schemas.py                 # Pydantic models
│   │   └── database.py                # SQLAlchemy + pgvector
│   └── utils/
│       ├── award_classifier.py        # Query intent detection
│       └── rate_calculator.py         # Deterministic rate math
│
├── migrations/                        # Alembic DB migrations
│   └── versions/
│       └── 001_award_schema.py
│
├── scripts/
│   └── ingest_award.py                # One-shot CLI ingestion script
│
├── docker-compose.yml                 # PostgreSQL + pgvector
└── .env
```

---

## 6. Key Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| Vector DB | pgvector on PostgreSQL | You already have PostgreSQL; avoid new infra |
| Embedding model | text-embedding-3-small | Cost-effective, 1536-dim, strong performance |
| LLM | GPT-4o (or GPT-4o-mini) | Best citation adherence for legal/compliance text |
| Chunking strategy | Clause-boundary aware | Award has numbered clauses — respect structure |
| PDF parser | pdfplumber | Better table extraction than PyMuPDF |
| Retrieval | Hybrid (vector + BM25/FTS) | Legal text has exact terminology that vector search misses |
| Rate calculation | Deterministic SQL, not LLM | Never trust LLM for arithmetic in payroll |

---

## 7. Work Estimation

### Phase 1 — Ingestion Pipeline (Backend)
| Task | Hours |
|---|---|
| Set up pgvector, Alembic migrations, DB schema | 3 |
| PDF parser for MA000004 (pdfplumber + cleaning) | 4 |
| Semantic chunker with clause-boundary detection | 5 |
| Rate table extractor (parse schedule tables → SQL) | 6 |
| Embedding + pgvector insert pipeline | 3 |
| Ingestion API endpoint + error handling | 2 |
| **Phase 1 Total** | **23 hrs** |

### Phase 2 — RAG Query Pipeline (Backend)
| Task | Hours |
|---|---|
| Hybrid retriever (vector cosine + PostgreSQL FTS + RRF) | 5 |
| Query classifier / intent detector (age, day, time) | 4 |
| Prompt engineering + LLM integration | 4 |
| Deterministic rate calculator service | 6 |
| Rate API endpoint | 2 |
| Chat API endpoint + streaming | 3 |
| **Phase 2 Total** | **24 hrs** |

### Phase 3 — Frontend
| Task | Hours |
|---|---|
| Award upload + ingestion status page | 3 |
| Chat UI (streaming responses, citation display) | 5 |
| Rate calculator widget (form → structured result) | 4 |
| **Phase 3 Total** | **12 hrs** |

### Phase 4 — Testing & Validation
| Task | Hours |
|---|---|
| Ground-truth Q&A test suite (20+ queries) | 4 |
| Rate calculation accuracy tests vs Fair Work tables | 3 |
| End-to-end integration tests | 3 |
| **Phase 4 Total** | **10 hrs** |

### **Total Estimate: ~69 person-hours**
> At 10 hrs/week side-project pace → ~7 weeks
> At 15 hrs/week → ~5 weeks

---

## 8. Recommended Build Order

```
Week 1:  Docker + pgvector setup → PDF parser → basic chunker → embed + store
Week 2:  Rate table extractor → DB schema complete → ingest CLI script working
Week 3:  Hybrid retriever → rate calculator → chat API with basic prompting
Week 4:  Frontend chat UI → upload page → streaming responses
Week 5:  Rate calculator widget → citation display → test suite + fixes
```

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Award PDF has complex tables hard to parse | Use pdfplumber's `extract_tables()`; fall back to manual JSON for critical schedules |
| LLM hallucinates rates | Always verify with deterministic SQL rate lookup; LLM only explains, never calculates |
| Award gets updated by Fair Work | Build version-aware ingestion; store `effective_date` on all rate rows |
| Chunking splits related clauses | Use overlap (100 tokens) + metadata to link related chunks |

---

## 10. Quick-Start: First Coding Session

Install dependencies and get pgvector running:

```bash
# docker-compose.yml addition
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: payroll_dev
      POSTGRES_PASSWORD: dev_password

# Python deps
pip install fastapi uvicorn pdfplumber openai pgvector sqlalchemy alembic psycopg2-binary
```

First script to validate the pipeline end-to-end:

```python
# scripts/ingest_award.py
import pdfplumber, openai, psycopg2

def chunk_text(text, max_tokens=500):
    # Split on clause patterns like "18." or "Schedule B"
    import re
    splits = re.split(r'\n(?=\d+\.\d+|\bSchedule\b|\bAppendix\b)', text)
    return [s.strip() for s in splits if len(s.strip()) > 50]

def embed_and_store(chunks):
    client = openai.OpenAI()
    for chunk in chunks:
        resp = client.embeddings.create(model="text-embedding-3-small", input=chunk)
        embedding = resp.data[0].embedding
        # INSERT into award_chunks ...

with pdfplumber.open("MA000004.pdf") as pdf:
    full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

chunks = chunk_text(full_text)
embed_and_store(chunks)
print(f"Ingested {len(chunks)} chunks")
```
