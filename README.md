# MQC-AI (Manufacturing Quality Control AI)

## Project Overview

MQC-AI adalah sistem inspeksi kualitas produk berbasis *Computer Vision* end-to-end yang dirancang untuk otomasi deteksi cacat di lini produksi industri (misal: pelapisan/coating dan pengelasan). Proyek ini merupakan inisiatif untuk GSPE.

Sistem ini menggunakan arsitektur *decoupled* yang dipisahkan menjadi 3 komponen utama, namun dikelola dalam satu *repository* (monorepo). Inspector memantau live feed dari kamera, trigger pengiriman batch ke server SAM3 untuk analisis, lalu me-review hasil segmentasi cacat dan generate laporan audit.

## Arsitektur & Workspace

| Component | Status | Description |
|---|---|---|
| `qc_frontend/` | **Active** | Vue 3 dashboard dengan 6 halaman, Carbon Design System, i18n bilingual, live `qc_server` API integration, detection WebSocket overlay |
| `qc_server/` | **Active (M0-M3 + streaming slices 1-2)** | FastAPI + SQLite backend untuk async batch **defect** segmentation, CRUD metadata APIs, RTSP/USB camera streaming, detection WebSocket, real camera status monitor |
| `edge_app/` | Planned (after server) | Jetson Nano + TensorRT/`supervision` untuk **deteksi & penghitungan objek produk** + count-approval gate + live streaming |

### End-to-End Workflow

```
[Edge] Detect+Count product objects (.pt) → Crop → [Count Inspection Gate: approve]
    → [Trigger: POST /api/batches dengan folder crop]
    → [qc_server: async defect segmentation (pluggable: mock→SAM3 prompt), polling]
    → [QC Studio: Review defects (zoom/pan) + mark reviewed]
    → [Export: Crop/Full PNG + PDF Audit Report]
    → [Audit Log: auto-trails all actions]
```

Detail: [`docs/workflow.md`](./docs/workflow.md) | [`docs/PRD.md`](./docs/PRD.md)

> **Phase C-3 integration note:** The dashboard now uses the live `qc_server` API for QC Studio, Live Monitor's "Send to QC", Batch History, Reports, Audit Log, Cameras, and Settings via the Vite dev proxy (`/api` → `http://localhost:8787`, same-origin, no CORS). In the Send-to-QC dialog, **Source Folder (Crops)** is a path on the **server running `qc_server`**, not the browser machine. Settings now persists model configuration, confidence threshold, and `defect_strategy` to `/api/settings`.
>
> **Live Streaming Slice 2:** Live Monitor now consumes `WEBSOCKET /api/cameras/{id}/detect` for camera frames, detection boxes, and live object count. `GET /api/cameras/{id}/stream` remains available as the raw MJPEG fallback. Object detection uses server-only ML deps in `qc_server/requirements-ml.txt`; the server must set `MQC_MODEL_PATH=/path/to/model.pt`.
>
> **Phase C-2.1 review sign-off:** QC Studio has an explicit **"Mark Reviewed"** sign-off button (enabled only once every image is reviewed) that transitions a batch from `done` → `reviewed` (reviewer `inspector@gspemail.com`) and logs `BATCH_REVIEWED`. Batch History shows a **Reviewed (X/Y)** column and visually distinct pills: `done` is neutral, `reviewed` is green, `failed` is red. The backend `GET /api/batches` includes a computed `reviewed_count` per batch.

### Quick Start (Linux server)

```bash
git clone https://github.com/LyKhan77/MQC-AI.git && cd MQC-AI
bash scripts/setup.sh    # backend venv + deps, frontend deps, runs backend tests
bash scripts/dev.sh      # runs BE (:8787) + FE (:5757) together, combined [BE]/[FE] logs
```

Override ports with `BE_PORT=... FE_PORT=... bash scripts/dev.sh`. The setup script
targets Linux; on the Windows dev laptop use the per-workspace commands below.

## Frontend Dashboard (`qc_frontend/`)

### Tech Stack

- **Vue 3** (Composition API, `<script setup>`) + **Vite** + **Vue Router**
- **Carbon Design System** (IBM) dengan light mode (default) dan dark mode (Gray-100 theme)
- **Vanilla CSS** dengan CSS Variables (no Tailwind, no UI library)
- **IBM Plex Sans** + **IBM Plex Mono** fonts
- **jsPDF** untuk PDF audit report generation
- **Vitest** untuk unit testing

### Pages (6 routes)

| Route | Page | Description |
|---|---|---|
| `/live` | **Live Monitor** | Camera selector (RaspyCam/RTSP/USB), live detection canvas overlay, live object count, real online/offline status, Send to QC dialog |
| `/qc` | **QC Studio** | 3-column inspection: batch sidebar (filter/search) + canvas (zoom/pan) + defect panel (keyboard nav, review workflow) |
| `/batches` | **Batch History** | Searchable table of all processed batches, filter by status |
| `/reports` | **Reports** | PDF audit report generator with summary, defect table, approval fields |
| `/audit` | **Audit Log** | Auto-logged activity trail, filterable by action type |
| `/settings` | **Settings** | Camera CRUD, model config, defect strategy, language/theme preferences |

### Key Features

- **Bilingual i18n** (Bahasa Indonesia / English) dengan toggle, persisted di localStorage
- **Light/Dark mode toggle** dengan Carbon Gray-100 dark theme, persisted di localStorage
- **Collapsible sidebar navigation** dengan 6 menu items
- **Review workflow**: mark/unmark reviewed per image, progress bar, keyboard navigation
- **Zoom/Pan canvas**: mouse wheel zoom (50%-500%), drag to pan, annotation toggle
- **Live API-backed data**: cameras, settings, batches, reports, and audit logs load from `qc_server`; Live Monitor streams frames through the detection WebSocket and shows real camera status
- **Live detection/counting**: object boxes and live count render on a `<canvas>` from `WEBSOCKET /api/cameras/{id}/detect`; `single` count mode is per-frame, `tracking` is cumulative unique track IDs
- **Dynamic defect colors**: CSS variable resolution, siap untuk dynamic colors dari SAM3 backend

### Commands

> **Do not change** these command definitions without updating `AGENTS.md`.

| Command | Description |
|---|---|
| `cd qc_frontend && npm install` | Install dependencies |
| `cd qc_frontend && npm run dev` | Start Vite dev server (`http://localhost:5757`) |
| `cd qc_frontend && npm run build` | Production build to `dist/` |
| `cd qc_frontend && npm run preview` | Preview production build |
| `cd qc_frontend && npm test` | Run unit tests (Vitest) |

## Backend Server (`qc_server/`)

### Tech Stack

- **FastAPI** + **Uvicorn**
- **SQLAlchemy 2.0** + **SQLite**
- **Pydantic v2** + `pydantic-settings`
- **Pillow** for image metadata
- **OpenCV headless** for RTSP/USB camera probe + MJPEG frame encoding
- **Ultralytics + supervision** for server-side object detection/counting, installed separately from `requirements-ml.txt`
- **pytest** + FastAPI TestClient

### Commands

| Command | Description |
|---|---|
| `cd qc_server && python -m venv .venv` | Create backend virtualenv |
| `cd qc_server && .\.venv\Scripts\python.exe -m pip install -r requirements.txt` | Install backend dependencies |
| `cd qc_server && .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8787` | Start backend API |
| `cd qc_server && .\.venv\Scripts\python.exe -m pytest -v` | Run backend tests |

### Current Scope

Implemented M0-M3 plus Live Streaming Slices 1-2: health/startup, SQLite schema, seeded cameras/defect classes/settings, metadata CRUD, audit log, async batch polling, deterministic `mock` defect strategy, `result.json` output, crop image serving, `GET /api/cameras/{id}/stream` MJPEG streaming, `WEBSOCKET /api/cameras/{id}/detect` detection/counting stream, and background camera status monitoring. Real `sam3_prompt` inference is deferred to M4; crop/count-gate-to-QC is Slice 3.

Server-only detection dependencies are kept out of the laptop/base install. On the GPU server, install a CUDA-matched `torch` first, then `cd qc_server && .venv/bin/python -m pip install -r requirements-ml.txt`, set `MQC_MODEL_PATH`, and run the backend.

## Design System

Frontend menggunakan **Carbon Design System** (IBM) dengan prinsip:
- Flat geometry (`border-radius: 0px`) dengan 1px hairline borders
- IBM Plex Sans weight 300 untuk display, 400 untuk body (`letter-spacing: 0.16px`)
- IBM Blue (`#0f62fe`) sebagai single accent color
- Surface hierarchy via `--color-canvas` / `--color-surface-1` / hairlines (no drop shadows)
- Light mode (default) + Dark mode (Carbon Gray-100 theme)

Detail lengkap: [`DESIGN.md`](./DESIGN.md)

## Documentation

| Document | Purpose |
|---|---|
| [`AGENTS.md`](./AGENTS.md) | Agent operating manual (project overview, tech stack, conventions, current state) |
| [`CHANGELOG.md`](./CHANGELOG.md) | Detailed change log with Current Codebase State table (agent memory contract) |
| [`DESIGN.md`](./DESIGN.md) | Carbon Design System spec (colors, typography, components, light/dark tokens) |
| [`docs/PRD.md`](./docs/PRD.md) | Product Requirements Document |
| [`docs/workflow.md`](./docs/workflow.md) | System workflow and architecture diagram |
| `docs/superpowers/plans/` | Implementation plans (gitignored, not committed) |

## Implementation Plans

Rencana implementasi disimpan di `docs/superpowers/plans/` (gitignored):
- `frontend-overhaul-plan.md` - Full frontend overhaul (Carbon Design System, 6 pages, i18n, mock data)
- `qc-server-plan.md` - Backend `qc_server` plan: locked decisions, folder structure, SQLite schema, endpoints, pluggable defect strategy, milestones M0→M4 (+ edge flow reference)
- `2026-06-27-phase-c3-cameras-settings.md` - Cameras + Settings live API integration plan
- `2026-06-28-live-streaming-slice1.md` - RTSP/USB camera MJPEG streaming + real online/offline status

---
*Dokumen ini harus selalu diperbarui setiap kali ada penambahan fitur utama atau perubahan arsitektur. Lihat protocol di `AGENTS.md` > Documentation Maintenance.*
