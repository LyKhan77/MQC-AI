# qc_server - MQC-AI Backend (SAM3 Defect Segmentation)

FastAPI + SQLite backend. Ingests folders of cropped product images, runs an
async (polling) defect pipeline (currently the `mock` strategy), and serves
results + image files to the Vue frontend.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the interactive API.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Defect strategy

Selected via `GET/PUT /api/settings` (`defect_strategy`). Implemented now:
`mock`. The `app/services/inference/` interface allows adding `sam3_prompt`
(real SAM3) and others without changing the API. See
`docs/superpowers/plans/qc-server-plan.md`.

## Configuration

Copy `.env.example` to `.env` and adjust (`MQC_DATABASE_URL`, `MQC_DATA_DIR`,
`MQC_REVIEWER_EMAIL`, `MQC_CORS_ORIGINS`).
