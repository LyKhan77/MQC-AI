# MQC-AI (Manufacturing Quality Control AI)

## Project Overview

MQC-AI adalah sistem inspeksi kualitas produk berbasis *Computer Vision* end-to-end yang dirancang untuk otomasi deteksi cacat di lini produksi industri (misal: pelapisan/coating dan pengelasan). Proyek ini merupakan inisiatif untuk GSPE.

Sistem ini menggunakan arsitektur *decoupled* yang dipisahkan menjadi 3 komponen utama, namun dikelola dalam satu *repository* (monorepo). Inspector memantau live feed dari kamera, trigger pengiriman batch ke server SAM3 untuk analisis, lalu me-review hasil segmentasi cacat dan generate laporan audit.

## Arsitektur & Workspace

| Component | Status | Description |
|---|---|---|
| `qc_frontend/` | **Active** | Vue 3 dashboard dengan 7 halaman, Carbon Design System, i18n bilingual, live `qc_server` API integration, Auto/Manual Live Monitor, annotated MJPEG detection feed/count/FPS, Send-to-QC crop approval gate, Detection Test upload page |
| `qc_server/` | **Active (M0-M3 + streaming slices 1-3 + Auto/Manual redesign)** | FastAPI + SQLite backend untuk async batch **defect** segmentation, CRUD metadata APIs, RTSP/USB camera streaming, annotated MJPEG detection/counting/FPS, one-shot capture, per-camera crop sessions, crop approval endpoints, sample image/video detection test endpoints, real camera status monitor |
| `edge_app/` | Planned (after server) | Jetson Nano + TensorRT/`supervision` untuk **deteksi & penghitungan objek produk** + count-approval gate + live streaming |

### End-to-End Workflow

```
[Live Monitor] Start Camera raw preview
    → [Auto: Start/Stop Detection | Manual: Capture x N]
    → [Review & approve crop grid]
    → [Trigger: POST /api/batches dengan approved crop folder]
    → [qc_server: async defect segmentation (pluggable: mock→SAM3 prompt), polling]
    → [QC Studio: Review defects (zoom/pan) + mark reviewed]
    → [Export: Crop/Full PNG + PDF Audit Report]
    → [Audit Log: auto-trails all actions]
```

Detail: [`docs/workflow.md`](./docs/workflow.md) | [`docs/PRD.md`](./docs/PRD.md)

> **Phase C-3 integration note:** The dashboard now uses the live `qc_server` API for QC Studio, Live Monitor's "Send to QC", Batch History, Reports, Audit Log, Cameras, and Settings via the Vite dev proxy (`/api` → `http://localhost:8787`, same-origin, no CORS). Settings now persists model configuration, confidence threshold, and `defect_strategy` to `/api/settings`.
>
> **Live Streaming Slice 2.3:** Live Monitor consumes annotated MJPEG from `GET /api/cameras/{id}/detect-stream`; the browser renders it as an `<img>`, while the metric strip polls `GET /api/cameras/{id}/count` for `{ count, fps }`. The detection stream downscales before inference and caps loop FPS via `MQC_STREAM_MAX_WIDTH` / `MQC_STREAM_MAX_FPS` (defaults: `960` / `15`). `GET /api/cameras/{id}/stream` remains available as the raw MJPEG fallback. Drop YOLO `.pt` weights into `qc_server/models/`, then choose the active file in **Settings -> Model Configuration -> Active Model**. Object detection uses server-only ML deps in `qc_server/requirements-ml.txt`.
>
> **Live Monitor Auto/Manual Flow:** Start Camera resets a per-camera crop session and shows raw MJPEG preview. Auto runs `GET /api/cameras/{id}/detect-stream` until Stop Detection; Manual calls `POST /api/cameras/{id}/capture` per click. Review & Send calls `POST /api/cameras/{id}/crop-session/finalize`, lets the operator check selected crop thumbnails, then calls `POST /api/cameras/{id}/crop-session/approve` and submits `POST /api/batches` with the approved crop folder.
>
> **Detection Test Slice 2.4:** Settings includes **Enable Detection Test page** (`input_mode_enabled`) to show/hide `/detect-test` in the sidebar. The page uploads an image to `POST /api/detect/image` for an annotated base64 result + detection list, or uploads a video to `POST /api/detect/video` and plays `GET /api/detect/video/{id}/stream` as annotated MJPEG. Uploaded videos are stored under `qc_server/data/uploads/`, which stays gitignored. GPU/model smoke is run on the server.
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
- **Vitest** + **Vue Test Utils** + **jsdom** untuk unit/component testing

### Pages (7 routes)

| Route | Page | Description |
|---|---|---|
| `/live` | **Live Monitor** | Camera selector (RaspyCam/RTSP/USB), Start Camera raw preview, Auto annotated MJPEG detection, Manual capture, live object count/FPS, real online/offline status, Send to QC crop approval dialog |
| `/qc` | **QC Studio** | 3-column inspection: batch sidebar (filter/search) + canvas (zoom/pan) + defect panel (keyboard nav, review workflow) |
| `/batches` | **Batch History** | Searchable table of all processed batches, filter by status |
| `/detect-test` | **Detection Test** | Server-gated upload page for testing the active model on sample images/videos |
| `/reports` | **Reports** | PDF audit report generator with summary, defect table, approval fields |
| `/audit` | **Audit Log** | Auto-logged activity trail, filterable by action type |
| `/settings` | **Settings** | Camera CRUD, active detection model switcher, decimal confidence, defect strategy, language/theme preferences |

### Key Features

- **Bilingual i18n** (Bahasa Indonesia / English) dengan toggle, persisted di localStorage
- **Light/Dark mode toggle** dengan Carbon Gray-100 dark theme, persisted di localStorage
- **Collapsible sidebar navigation** dengan 7 menu items when Detection Test is enabled
- **Review workflow**: mark/unmark reviewed per image, progress bar, keyboard navigation
- **Zoom/Pan canvas**: mouse wheel zoom (50%-500%), drag to pan, annotation toggle
- **Live API-backed data**: cameras, settings, batches, reports, and audit logs load from `qc_server`; Live Monitor streams raw/annotated MJPEG frames, shows real camera status, and sends approved crop folders to QC
- **Live detection/counting/FPS**: object boxes and count overlay are drawn server-side in Auto via `GET /api/cameras/{id}/detect-stream`; the UI polls `GET /api/cameras/{id}/count` for count and real stream FPS; Manual uses one-shot `POST /api/cameras/{id}/capture`
- **Count-gate crop approval**: `POST /api/cameras/{id}/crop-session/finalize` prepares server-side object crops, `POST /api/cameras/{id}/crop-session/approve` copies selected crops, and Send to QC submits only the approved folder
- **Active model switcher**: `.pt` files in `qc_server/models/` are listed by `GET /api/models`; Settings persists the chosen file as `active_model` and shows confidence as decimal `0.00-1.00`
- **Detection Test page**: gated by `input_mode_enabled`; uploads sample images/videos to `/api/detect/*` and renders annotated results from the active model
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

Implemented M0-M3 plus Live Streaming Slices 1-3 and the Auto/Manual redesign: health/startup, SQLite schema, seeded cameras/defect classes/settings, metadata CRUD, audit log, async batch polling, deterministic `mock` defect strategy, `result.json` output, crop image serving, `GET /api/cameras/{id}/stream` raw MJPEG streaming, `GET /api/cameras/{id}/detect-stream` annotated MJPEG detection/counting stream with downscale/FPS cap, `GET /api/cameras/{id}/count` returning count and FPS, one-shot `grab_one()` capture, per-camera crop sessions, `POST /api/cameras/{id}/crop-session/start`, `POST /api/cameras/{id}/capture`, `POST /api/cameras/{id}/crop-session/finalize`, `POST /api/cameras/{id}/crop-session/approve`, crop thumbnail serving, `/api/detect/*` sample image/video detection endpoints, and background camera status monitoring. Real `sam3_prompt` inference is deferred to M4.

Detection stream performance is configured with `MQC_STREAM_MAX_WIDTH` (default `960`) and `MQC_STREAM_MAX_FPS` (default `15`). Downscaling happens before detection so drawn boxes match the streamed frame.

Crop sessions store source images under `qc_server/data/crops/<camera_id>/<session_ts>/`. Start Camera resets the session; Auto detection and Manual Capture append crops; Stop Detection leaves the buffer available for Review & Send; approved copies go under `approved/`.

Detection Test uploads require `python-multipart`. Images return annotated JPEG data and serialized detections. Videos are saved to `qc_server/data/uploads/` and streamed back as annotated MJPEG using the active model.

Server-only detection dependencies are kept out of the laptop/base install. On the GPU server, install a CUDA-matched `torch` first, then `cd qc_server && .venv/bin/python -m pip install -r requirements-ml.txt`, copy `.pt` weights into `qc_server/models/`, choose the active model in Settings, and run the backend.

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
- `2026-06-29-detection-mjpeg-rework.md` - Detection transport rework to annotated MJPEG + latest-frame grabber
- `2026-06-29-detection-ux-perf.md` - Detection UX polish, stream downscale/FPS cap, live FPS metric
- `2026-06-29-detection-test-page.md` - Detection Test page with image/video upload and server setting gate
- `2026-06-29-live-streaming-slice3-count-gate-crop-qc.md` - Count-gate crop capture and Send-to-QC review flow
- `2026-06-29-live-monitor-auto-manual-flow.md` - Live Monitor Start Camera, Auto/Manual, capture, and crop approval redesign

---
*Dokumen ini harus selalu diperbarui setiap kali ada penambahan fitur utama atau perubahan arsitektur. Lihat protocol di `AGENTS.md` > Documentation Maintenance.*
