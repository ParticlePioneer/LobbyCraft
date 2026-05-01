# LobbyCraft Matchmaking System

Database-driven multiplayer matchmaking system for **Battle Royale** and **Competitive Shooter** modes, built as a DBMS course project.

Tech stack:
- Python 3.12
- FastAPI
- Streamlit
- Oracle Database (Autonomous/FreeSQL compatible)

---

## 1) Project Overview

This project models the full matchmaking lifecycle:
- player registration and profile management
- party creation and queue entry
- criteria-based matchmaking sessions
- match/team/participant persistence
- post-match stats ingestion and MMR updates
- analytics (leaderboards, lobby quality, MMR history)

It includes:
- normalized Oracle schema (BCNF-oriented design)
- stored procedures for session and queue operations
- REST API layer
- Streamlit dashboard
- test suite with `pytest`

---

## 2) Python Compatibility

This project is set up to run with **Python 3.12**.

Check your version:

```powershell
python --version
```

Expected: `Python 3.12.x`

---

## 3) Prerequisites

Install:
- Python 3.12
- Oracle DB access (Autonomous DB / Oracle FreeSQL / local Oracle)
- `pip` (bundled with Python)

Optional but recommended:
- SQL Developer or SQLcl for running SQL files

---

## 4) Clone and Setup

From project root (`matchmaking`):

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS/Linux (bash/zsh)

```bash
python3.12 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5) Environment Variables (`.env`)

Create a `.env` file in the project root:

```env
oracle_user=YOUR_DB_USERNAME
oracle_password=YOUR_DB_PASSWORD
oracle_dsn=YOUR_DB_DSN
api_host=0.0.0.0
api_port=8000
```

### `oracle_dsn` examples

- Easy Connect style:
  - `host:port/service_name`
- Autonomous DB format (example):
  - `adb.region.oraclecloud.com:1522/xxxx_high.adb.oraclecloud.com`

> Make sure the credentials in `.env` have permission to create tables, sequences, procedures, and indexes.

---

## 6) Database Initialization

You must run schema scripts once before starting API/UI.

SQL files:
- `db/ddl.sql` (tables, constraints, indexes, sequences)
- `db/seed.sql` (lookup and initial rows)
- `db/procedures.sql` (PL/SQL procedures)

### Option A: SQL*Plus / SQLcl

```sql
@db/ddl.sql
@db/seed.sql
@db/procedures.sql
```

### Option B: SQL Developer
Open each file and execute in this order:
1. `db/ddl.sql`
2. `db/seed.sql`
3. `db/procedures.sql`

---

## 7) Run the Backend API

From project root (with venv active):

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs:
- Swagger UI: <http://localhost:8000/docs>

Root endpoint redirects to docs.

---

## 8) Run the Streamlit UI

In a second terminal (venv active):

```powershell
streamlit run streamlit_app.py
```

Default UI URL:
- <http://localhost:8501>

Main pages:
- Players
- Parties & Queue
- Match Results
- Analytics

---

## 9) Seeding Data

### Quick scenario seed

Creates players, parties, queue entries, assembles one match, submits random results:

```powershell
python seed_db.py
```

### Large dataset seed

Generates many players and matches for analytics/load-style testing:

```powershell
python seed_massive.py
```

---

## 10) Run Tests

With API dependencies installed and DB configured:

```powershell
pytest -q
```

Test file:
- `tests/test_api.py`

Current tests cover:
- player creation and duplicate prevention
- party creation
- queue enqueue and duplicate queue rejection
- MMR history endpoint behavior
- timeout expiration endpoint
- leaderboard endpoint

---

## 11) Core API Route Groups

- `/players`
  - create player
  - get player
  - get MMR history
  - set role preference
- `/parties`
  - create party
  - get party
  - get party members
- `/queue`
  - enqueue party
  - waiting monitor
  - expire stale queue entries
- `/matches`
  - get match
  - get participants
  - submit/finalize results
  - lobby quality analytics
  - leaderboard

Use Swagger for exact request/response schemas:
- <http://localhost:8000/docs>

---

## 12) Recommended Run Order (First-Time Setup)

1. Create and activate virtual environment  
2. Install requirements  
3. Create `.env`  
4. Execute SQL scripts (`ddl.sql`, `seed.sql`, `procedures.sql`)  
5. Start FastAPI (`uvicorn ...`)  
6. Start Streamlit (`streamlit run streamlit_app.py`)  
7. (Optional) Run `seed_db.py` or `seed_massive.py`  
8. (Optional) Run tests (`pytest -q`)  

---

## 13) Common Troubleshooting

### A) `RuntimeError: Pool not initialised`
- Ensure API starts through `main.py` (lifespan initializes pool)
- Confirm `.env` exists and values are valid

### B) Oracle authentication / DSN errors
- Recheck `oracle_user`, `oracle_password`, `oracle_dsn`
- Verify network/firewall access to DB host and port
- Verify DB user privileges

### C) UI says API offline
- Ensure backend is running on `http://localhost:8000`
- Check `uvicorn` terminal for startup errors

### D) `table or view does not exist`
- Re-run DB scripts in correct order:
  1) `db/ddl.sql`
  2) `db/seed.sql`
  3) `db/procedures.sql`

### E) `pytest` failures caused by DB state
- Ensure database is reachable
- Ensure schema + seed scripts are already applied

---

## 14) Project Structure

```text
matchmaking/
├─ api/                  # FastAPI route modules
├─ dal/                  # Data access layer
├─ db/                   # DB connection + SQL scripts
├─ engine/               # Matchmaking/MMR logic
├─ models/               # Entity models
├─ pages/                # Streamlit multipage views
├─ tests/                # Pytest tests
├─ main.py               # FastAPI app entry
├─ streamlit_app.py      # Streamlit app entry
├─ seed_db.py            # scenario seed
├─ seed_massive.py       # large seed
└─ requirements.txt
```

---

## 15) Notes

- Keep secrets only in `.env` (never commit credentials).
- If you modify schema, re-validate APIs and tests.
- For grading/demo, keep API + Streamlit running simultaneously.

