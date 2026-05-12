# LobbyCraft — Matchmaking System

Database-backed multiplayer matchmaking for **Battle Royale** and **Competitive Shooter** modes (DBMS course project: **LobbyCraft**).

| Layer | Technology |
|-------|------------|
| Runtime | **Python 3.12** |
| API | **FastAPI** (`uvicorn`) |
| UI | **Streamlit** (multipage app) |
| Database | **Oracle** (Autonomous / FreeSQL / compatible; `oracledb`) |

---

## Overview

The system covers the full matchmaking lifecycle:

- **Players** — registration, regions, MMR snapshot, optional role preferences  
- **Parties** — solo / duo / squad and membership  
- **Queues & modes** — enqueue by `mode_id`, duplicate-queue guards, wait monitoring, stale expiration  
- **Sessions & matches** — criteria-bound sessions, lobby assembly, teams and participants  
- **Results & rating** — post-match stats, MMR deltas, history reconstruction  
- **Analytics** — leaderboards, lobby fairness (`lobby-quality`), MMR trends  

### Architecture highlights

- **Relational core (Oracle)** — normalized schema, sequences, constraints, indexes; optional PL/SQL procedures under `db/procedures.sql`.  
- **Pluggable matchmaking engines** — engines are registered in the DB (`MATCHMAKING_ENGINE`, `ENGINE_PARAMETER`); **criteria** rows bind each mode’s policy to an **engine** (`MATCHMAKING_CRITERIA.engine_id`). The API resolves and loads the correct Python engine class at runtime (`engine/loader.py`).  
- **Rating policies** — separated from lobby assembly; configurable per engine parameters (see engine docs in code).  

Optional **future / hybrid** extensions (described in project documentation, not required to run this repo):

- **MongoDB** — denormalized read models (e.g. match detail documents).  
- **ChromaDB** — vector indexes for similarity/analytics experiments (not wired by default).

---

## Prerequisites

- **Python 3.12** (`python --version` → `Python 3.12.x`)  
- Oracle database reachable from your machine  
- **`pip`** (comes with Python)  

Recommended for DB setup:

- SQL Developer, SQLcl, or SQL*Plus to run `db/*.sql`

---

## Quick start

### 1. Clone / open project

```powershell
cd "D:\DBMS project\matchmaking"
```

### 2. Virtual environment & dependencies

**Windows (PowerShell)**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3.12 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment file

Create `.env` in the project root:

```env
oracle_user=YOUR_DB_USERNAME
oracle_password=YOUR_DB_PASSWORD
oracle_dsn=YOUR_DB_DSN
api_host=0.0.0.0
api_port=8000
```

**`oracle_dsn` examples**

- Easy Connect: `host:port/service_name`  
- Autonomous DB (shape): `adb.region.oraclecloud.com:1522/your_service.adb.oraclecloud.com`  

The DB user must be able to create tables, sequences, indexes, and procedures (as defined in `db/ddl.sql`).

### 4. Initialize the database

Execute **in order**:

1. `db/ddl.sql` — schema (includes engine tables if your revision matches the repo)  
2. `db/seed.sql` — reference data (modes, roles, criteria, etc.)  
3. `db/procedures.sql` — stored procedures (session / queue / finalize)  

If your instructor provides additional **`engine_*`** seed scripts, run them after `seed.sql` so `MATCHMAKING_ENGINE` / `ENGINE_PARAMETER` and `criteria.engine_id` are populated.

**SQL*Plus / SQLcl**

```sql
@db/ddl.sql
@db/seed.sql
@db/procedures.sql
```

### 5. Run the API

From project root with venv active:

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger UI: <http://localhost:8000/docs>  
- Root `/` redirects to `/docs`  

Using `python -m uvicorn` avoids PATH issues when `uvicorn` is not on `PATH`.

### 6. Run the Streamlit UI (second terminal)

```powershell
streamlit run streamlit_app.py
```

Default: <http://localhost:8501>  

Pages typically include Players, Parties & Queue, Match Results, Analytics, and **Engine Lab** (if present).

---

## Multi-engine configuration (summary)

| Concept | Location |
|--------|-----------|
| Engine registry | `MATCHMAKING_ENGINE` (`engine_id`, `engine_name`, `engine_class`, `is_active`) |
| Tunables | `ENGINE_PARAMETER` (`engine_id`, `param_key`, `param_value`, `param_type`) |
| Policy → engine | `MATCHMAKING_CRITERIA.engine_id` → chosen implementation |
| Loader | `engine/loader.py` — loads Python class from `engine_class`, merges parameters |

REST routes under **`/engines`** (see `api/engines.py`) support listing engines, viewing mode–criteria–engine mappings, and updating which engine is assigned to a criteria row (for demos / experiments).

Queue handling (`api/queue.py`) resolves criteria, loads the engine, and runs `engine/matchmaker.py::assemble_lobby`.

---

## Optional: MongoDB & ChromaDB (documentation / future work)

This repository’s **runtime path is Oracle + FastAPI**. For coursework or scaling narratives you may document:

| Store | Typical use |
|-------|-------------|
| **MongoDB** | Denormalized documents for match detail, player profiles with embedded recent matches, engine config snapshots for fast reads |
| **ChromaDB** | Vector embeddings for similarity search (e.g. behavioral similarity, anomaly clustering) — auxiliary to transactional Oracle data |

A safe production pattern is **Oracle as source of truth** plus derived MongoDB views and optional vector indexes — not a replacement for FK integrity on day one.

---

## Data seeding & demos

| Script | Purpose |
|--------|---------|
| `seed_db.py` | Small scripted flow: players, party, queue, match assembly, sample results |
| `seed_massive.py` | Larger synthetic dataset for analytics / load-style experiments |

```powershell
python seed_db.py
python seed_massive.py
```

---

## Testing & sanity checks

**Automated API tests**

```powershell
pytest -q
```

Primary suite: `tests/test_api.py` (players, parties, queue, MMR history, expire-timeouts, leaderboard).

**End-to-end smoke (requires API running)**

```powershell
python -m tests.sanity
```

Uses `http://localhost:8000` — start `uvicorn` first.

---

## Main API surface

| Prefix | Purpose |
|--------|---------|
| `/players` | CRUD-ish player ops, MMR history, role preferences |
| `/parties` | Create party, members |
| `/queue` | Enqueue, waiting monitor, expire timeouts |
| `/matches` | Match detail (with mode / participants / winner where implemented), results, lobby quality, leaderboard |
| `/engines` | Engine registry and criteria ↔ engine assignment |

Full schemas: **Swagger** at `/docs`.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| `RuntimeError: Pool not initialised` | Start app via `main.py` so lifespan runs; valid `.env` |
| Oracle login / DSN errors | Credentials, network, wallet if Autonomous |
| `table or view does not exist` | Run `ddl.sql` → `seed.sql` → `procedures.sql` in order |
| UI “API offline” | API on port **8000**, no firewall block |
| Engine errors at enqueue | `MATCHMAKING_CRITERIA.engine_id` set; row in `MATCHMAKING_ENGINE`; `ENGINE_PARAMETER` if required |
| `uvicorn` not found | Use `python -m uvicorn ...` from activated venv |
| pytest fails | DB up, schema seeded, same `.env` as manual runs |

---

## Project layout

```text
matchmaking/
├── api/              # FastAPI routers (players, parties, queue, matches, engines)
├── dal/              # Data access layer
├── db/               # connection.py, ddl.sql, seed.sql, procedures.sql
├── engine/           # Engines, loader, matchmaker orchestration, rating helpers
├── models/           # Dataclasses / entities
├── pages/            # Streamlit pages
├── tests/            # pytest + sanity script
├── main.py           # FastAPI entry + lifespan pool
├── streamlit_app.py  # Streamlit entry
├── seed_db.py
├── seed_massive.py
├── config.py         # pydantic-settings / .env
└── requirements.txt
```

---

## Security & hygiene

- Do **not** commit `.env` or credentials.  
- Treat production Oracle credentials separately from coursework DBs.  
- After schema changes, rerun migrations/seeds and `pytest`.

---

## Course / report alignment

This README matches the implemented stack: **Oracle relational model**, **multi-engine criteria binding**, **FastAPI + Streamlit**, **Python 3.12**. Sections on **MongoDB** and **ChromaDB** describe optional hybrid extensions suitable for architecture discussion in reports, not mandatory dependencies for running this repo.
