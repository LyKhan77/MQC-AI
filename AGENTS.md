# MQC-AI — Agent & Project Operating Manual

<!-- LIVING DOCUMENT: All sections above the ==== divider are [KEEP UPDATED]. -->
<!-- Edit them whenever the codebase changes. See "Documentation Maintenance"  -->
<!-- at the bottom of this file for the update protocol.                       -->
<!-- The RULES section and behavioral guidelines below the ==== dividers are    -->
<!-- generic agent rules and should not be edited.                              -->

README.md is the canonical, detailed project doc. AGENTS.md orients an agent fast. CHANGELOG.md is the detailed change memory. Most sections below summarize README and link to it.

---

## Project Overview · `[KEEP UPDATED]`

**MQC-AI (Manufacturing Quality Control AI)** is an end-to-end computer vision system for automating defect detection in industrial production lines (coating and welding). Built for GSPE.

The system has three decoupled components managed in one monorepo:

1. **`qc_frontend/`** — Interactive dashboard for live camera monitoring and batch QC inspection review. **(Active; live API-backed dashboard data)**
2. **`qc_server/`** — Backend server for async batch defect segmentation. **(Active: M0-M3 done with mock strategy)**
3. **`edge_app/`** — Jetson Nano edge app for real-time object detection (YOLO) and live streaming. **(Not yet started)**

**End-to-end workflow**: Edge app detects objects on the production line and live-streams to the dashboard. Inspector monitors the live feed, triggers batch processing, reviews SAM3 segmentation results in QC Studio, and exports PDF audit reports.

Full specs: [`docs/PRD.md`](./docs/PRD.md) | [`docs/workflow.md`](./docs/workflow.md)

---

## Tech Stack · `[KEEP UPDATED]`

### Frontend (`qc_frontend/`)

| Layer | Technology | Version |
|---|---|---|
| Framework | Vue 3 (Composition API, `<script setup>`) | ^3.5 |
| Build tool | Vite | ^8.1 |
| Router | Vue Router | ^4.6 |
| Fonts | IBM Plex Sans + IBM Plex Mono (`@fontsource`) | ^5.2 |
| PDF generation | jsPDF (dynamic import) | ^4.2 |
| Testing | Vitest | ^4.1 |
| CSS | Vanilla CSS with CSS Variables (no Tailwind, no UI library) | — |
| Design system | Carbon Design System (IBM) with light/dark mode | — |

### Backend (`qc_server/`)

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | SQLite via SQLAlchemy 2.0 |
| Schemas/config | Pydantic v2 + pydantic-settings |
| Image metadata | Pillow |
| Camera streaming | OpenCV headless (`opencv-python-headless`) |
| Object detection/counting | Ultralytics + supervision (server-only `requirements-ml.txt`, lazy imports) |
| Testing | pytest + FastAPI TestClient |
| Defect strategy | Pluggable interface, `mock` implemented; `sam3_prompt` deferred |

### Edge (`edge_app/` — planned)

| Layer | Technology |
|---|---|
| Runtime | Python |
| Inference | TensorRT |
| Video | OpenCV |
| Stream server | Flask / FastAPI (MJPEG / WebSocket / WebRTC) |

---

## Key Features · `[KEEP UPDATED]`

### Frontend (current)

- **Sidebar navigation shell** (collapsible) with 6 pages.
- **Live Monitor**: API-backed camera selector (RaspyCam/RTSP/USB), real detection WebSocket canvas feed with bounding-box overlay and live object count, real online/offline camera status, Start/Stop trigger, Send to QC dialog with batch name + auto-timestamp.
- **QC Studio**: 3-column layout with batch sidebar (filter/search/sort/skeleton loading), inspection canvas (zoom/pan/annotation toggle), defect panel (keyboard navigation, review workflow).
- **Batch History**: searchable/filterable table of all processed batches, click to reopen in QC Studio.
- **Reports**: PDF audit report generator (batch summary, defect table, signature/approval fields) via jsPDF.
- **Audit Log**: auto-logged activity trail (all user actions across the app).
- **Settings**: API-backed camera CRUD, active detection model switcher, model config (confidence threshold, detection/segmentation model, defect strategy), preferences (language, theme).
- **Bilingual i18n** (Bahasa Indonesia / English) with toggle, persisted in localStorage.
- **Light/Dark mode** toggle (Carbon Gray-100 dark theme), persisted in localStorage.

### Backend (current — `qc_server` M0-M3)

- FastAPI backend under `qc_server/` with `/health`, startup table creation, CORS, and `.env` config.
- SQLite metadata for cameras, defect classes, settings, audit logs, batches, images, and defects.
- CRUD APIs for cameras, defect classes, settings, and audit logs.
- OpenCV-backed camera probe + MJPEG stream endpoint (`GET /api/cameras/{camera_id}/stream`), detection/counting WebSocket endpoint (`WEBSOCKET /api/cameras/{camera_id}/detect`), and background camera status monitor.
- Server-only object detection dependencies in `requirements-ml.txt`; `qc_server/models/*.pt` files are listed by `/api/models`, Settings persists `active_model`, and ML imports stay lazy for laptop tests.
- Async batch **defect** segmentation over crop folders via **polling** (`job_id` → poll status).
- Pluggable defect strategy interface with deterministic `mock` strategy implemented; real `sam3_prompt` deferred to M4.
- Filesystem result output under `qc_server/data/batches/<batch_id>/result.json` and crop serving via `/api/images/{image_id}/file`.

### Edge (planned — after qc_server)

- Real-time **object (product) detection + counting** on Jetson Nano from trained `.pt` (Detection/Segmentation), using `supervision`.
- Per-camera count mode: `tracking` (ByteTrack + LineZone/PolygonZone) or `single` (1-frame-1-object).
- **Count inspection gate**: technician approves count, then triggers `POST /api/batches` with crop folder path.
- Auto-crop detected objects (bbox/mask) to shared NAS storage.
- Live video stream (MJPEG/WebRTC) to dashboard.

---

## Project Structure · `[KEEP UPDATED]`

```
MQC-AI/
├── qc_frontend/               # Vue 3 dashboard (active development)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   │   ├── favicon.svg
│   │   └── mock/
│   │       ├── batch-shift1.json    # Mock batch data (3 images)
│   │       └── images/              # Mock product images
│   └── src/
│       ├── main.js                  # App entry
│       ├── App.vue                  # Root: sidebar + topbar shell
│       ├── style.css                # Carbon CSS variables (light/dark) + shared styles
│       ├── api/
│       │   ├── client.js            # HTTP helpers (GET/POST/PATCH/PUT/DELETE)
│       │   ├── audit.js             # Audit log API
│       │   ├── batches.js           # Batch submit/status/result/list/review API
│       │   ├── cameras.js           # Camera CRUD API
│       │   ├── models.js            # Detection model list API
│       │   └── settings.js          # Settings API with snake/camel mapping
│       ├── router/
│       │   └── index.js             # 6 named routes
│       ├── assets/
│       │   └── locales/
│       │       ├── id.js            # Indonesian translations (~300 strings)
│       │       └── en.js            # English translations
│       ├── components/
│       │   ├── AppSidebar.vue       # Collapsible nav (6 menu items)
│       │   ├── TopBar.vue           # Slim top bar (title, theme, i18n, profile)
│       │   ├── BatchSidebar.vue     # Batch list with filter/search/review progress
│       │   ├── InspectionCanvas.vue # Image canvas with zoom/pan/annotation
│       │   └── DefectPanel.vue      # Defect details + export + keyboard nav
│       ├── composables/
│       │   ├── useTheme.js          # Light/dark theme toggle (localStorage)
│       │   ├── useI18n.js           # ID/EN language toggle (localStorage)
│       │   ├── useInspection.js     # Batch loading, image selection, review workflow
│       │   ├── useCameras.js        # Camera CRUD (live API)
│       │   ├── useBatchHistory.js   # Batch history list (live API)
│       │   ├── useAuditLog.js       # Audit trail logging (live API + local cache)
│       │   └── useSettings.js       # Model config + defect strategy (live API)
│       ├── views/
│       │   ├── LiveMonitor.vue      # Camera selector + detection + send-to-QC
│       │   ├── QCStudio.vue         # 3-column inspection studio
│       │   ├── BatchHistory.vue     # Batch table with search/filter
│       │   ├── Reports.vue          # PDF report generator
│       │   ├── AuditLog.vue         # Activity log table
│       │   └── Settings.vue         # Camera CRUD + model config + preferences
│       └── utils/
│           ├── defect.js            # Defect type -> CSS variable color mapping
│           ├── export.js            # Canvas render + crop/full export (dynamic color)
│           └── mockData.js          # Seed data (3 cameras, 5 batches, 15 logs)
├── qc_server/                # FastAPI backend (M0-M3 done, mock strategy)
│   ├── requirements.txt
│   ├── requirements-ml.txt
│   ├── models/
│   │   └── README.md                # Drop .pt weights here; weights are gitignored
│   ├── pyproject.toml
│   ├── .env.example
│   ├── README.md
│   ├── app/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── storage.py
│   │   ├── routers/
│   │   │   ├── audit.py
│   │   │   ├── batches.py
│   │   │   ├── cameras.py
│   │   │   ├── defect_classes.py
│   │   │   ├── images.py
│   │   │   ├── models.py            # GET /api/models
│   │   │   └── settings.py
│   │   └── services/
│   │       ├── camera_monitor.py    # Background camera reachability polling
│   │       ├── counting.py          # Pure single/tracking object count helpers
│   │       ├── detect_stream.py     # Detection WS frame/message producer
│   │       ├── job_queue.py
│   │       ├── pipeline.py
│   │       ├── seed.py
│   │       ├── streaming.py         # OpenCV RTSP/USB probe + MJPEG frame generator
│   │       └── inference/
│   │           ├── __init__.py      # Lazy YOLO object detection + serialization
│   │           ├── base.py
│   │           └── mock.py
│   └── tests/
├── edge_app/                 # Jetson Nano edge app (not yet started)
├── docs/
│   ├── PRD.md                # Product Requirements Document
│   ├── workflow.md           # System workflow + architecture diagram
│   └── superpowers/
│       └── plans/            # Implementation plans (gitignored, not committed)
├── DESIGN.md                 # Carbon Design System spec (light/dark tokens)
├── CHANGELOG.md              # Detailed change log + Current Codebase State table
├── README.md                 # Canonical project doc
├── AGENTS.md                 # This file
└── .gitignore
```

---

## Project Commands · `[KEEP UPDATED]`

Frontend commands run from `qc_frontend/`. Backend commands run from `qc_server/`.

| Command | Description |
|---|---|
| `npm install` | Install dependencies |
| `npm run dev` | Start Vite dev server (`http://localhost:5757`) |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview production build locally |
| `npm test` | Run unit tests (Vitest) |
| `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8787` | Start backend API |
| `.\.venv\Scripts\python.exe -m pytest -v` | Run backend tests |

**Do not change** these command definitions in `package.json` without updating this section.

---

## Coding Conventions · `[KEEP UPDATED]`

### Vue Components

- Use `<script setup>` Composition API (no Options API).
- Import composables at top: `import { useXxx } from '../composables/useXxx.js'`.
- One component per `.vue` file. File name = PascalCase.
- `<style scoped>` always. Use `var(--color-*)` tokens, never raw hex values.

### CSS

- **No Tailwind, no UI libraries.** Vanilla CSS only.
- All colors via CSS variables defined in `style.css` (`--color-primary`, `--color-ink`, etc.).
- Legacy aliases (`--bg-app`, `--text-primary`) map to new Carbon tokens for backward compat.
- `border-radius: 0px` on all components (Carbon flat geometry).
- `letter-spacing: 0.16px` on body text (Carbon precision detail).
- Fonts: `var(--font-sans)` (IBM Plex Sans), `var(--font-mono)` (IBM Plex Mono).

### Composables

- Singleton pattern: module-scoped `ref()` outside the exported function.
- API-backed composables expose `refresh()` and keep current/default state if the server is unreachable.
- `localStorage` is still used for UI preferences and local review/offline cache where already established.
- Each composable returns refs + methods, no state mutation from outside.

### i18n

- All user-facing text via `t('key.path')` from `useI18n`.
- Translation keys namespaced: `nav.*`, `live.*`, `qc.*`, `batches.*`, `reports.*`, `audit.*`, `settings.*`, `common.*`.
- Add new strings to both `id.js` and `en.js`.

### Defect Colors

- Defined as CSS variables (`--defect-scratch`, `--defect-porosity`, etc.) in `style.css`.
- `utils/defect.js` maps type string to CSS variable name.
- `utils/export.js` resolves via `getComputedStyle` for canvas rendering.
- **Will become dynamic** from SAM3 backend response in the future.

### File Naming

- Views: PascalCase (`LiveMonitor.vue`, `QCStudio.vue`).
- Components: PascalCase (`AppSidebar.vue`, `DefectPanel.vue`).
- Composables: camelCase with `use` prefix (`useTheme.js`, `useInspection.js`).
- Utils: camelCase (`defect.js`, `export.js`, `mockData.js`).
- Locales: lowercase ISO code (`id.js`, `en.js`).

---

## Workflow · `[KEEP UPDATED]`

### End-to-End System Workflow

```
[Camera List] → [Select Camera] → [Start Stream]
    → [Monitor Detection Canvas + Object Count + Camera Status]
    → [Send to QC: batch name + timestamp]
    → [SAM3 Batch Processing (backend)]
    → [QC Studio: Review defects + zoom/pan + mark reviewed]
    → [Export: Crop/Full PNG + PDF Audit Report]
    → [Audit Log: auto-trails all actions]
```

### Development Workflow (for AI agents)

1. Read `CHANGELOG.md` to understand current state.
2. Read the relevant section in this file.
3. Check `docs/superpowers/plans/` for any active implementation plan.
4. Make changes following Coding Conventions above.
5. Run `npm run build` and `npm test` to verify.
6. Update `CHANGELOG.md` with a new entry (see protocol at bottom of CHANGELOG.md).
7. Update relevant `[KEEP UPDATED]` sections in this file.
8. Update `README.md` if key features or architecture changed.
9. Commit with a descriptive message.

---

## Current State · `[KEEP UPDATED]`

### Status: Live Streaming Slice 2.1 Implemented · Backend M0-M3 Implemented

**What is developed now**: Frontend dashboard data is now backed by the live `qc_server` API for cameras, settings, batches, reports, audit log, and QC Studio flow. Live Monitor uses a backend WebSocket detection stream for frames, boxes, and live object count, with the Slice-1 MJPEG endpoint retained as raw fallback. Settings lists `.pt` files from `qc_server/models/` and persists the selected `active_model` used by live detection. **Backend (`qc_server`) M0-M3 plus Live Streaming Slices 1-2.1 are implemented**: FastAPI + SQLite metadata APIs, async batch pipeline, mock defect strategy, result JSON, crop image serving, OpenCV MJPEG streaming, detection/counting WebSocket, model-folder switcher, and background camera status monitoring. Real SAM3 (`sam3_prompt`) remains deferred to M4. Crop/count-gate-to-QC is Slice 3.

### Component Status

| Component | Status | Description |
|---|---|---|
| `qc_frontend/` | **Active** | 6 pages, Carbon Design System, i18n, live API-backed data, detection canvas feed/count, active model switcher. |
| `qc_server/` | **Active** | FastAPI + SQLite backend. M0-M3 + Live Streaming Slices 1-2.1 done; SAM3 deferred. |
| `edge_app/` | **Not started** | Jetson Nano YOLO detection + live streaming. Planned. |

### Frontend Page Status

| Page | Status | Mock Data | Backend Ready |
|---|---|---|---|
| Live Monitor | **Functional** | None for camera feed/counting | Camera list, detection WebSocket feed/count, real status, and Send to QC API wired; crop/count-gate is Slice 3 |
| QC Studio | **Functional** | None for live batches | Batch polling/result/review/sign-off API wired; real SAM3 deferred |
| Batch History | **Functional** | None | Live batch list API wired |
| Reports | **Functional** | None | Live batch/result API wired |
| Audit Log | **Functional** | Local cache fallback | Live audit API wired |
| Settings | **Functional** | None | Camera CRUD, settings API, and active detection model switcher wired |

### Detailed Log

See [`CHANGELOG.md`](./CHANGELOG.md) for the comprehensive, per-feature change log with Current Codebase State tables.

**Latest version**: [Unreleased] - 2026-06-29 (Live Streaming Slice 2.1: model folder, `/api/models`, active model switcher, guarded `active_model` migration).

---

## Documentation Maintenance

**This protocol is mandatory for all AI agents.**

### When to Update

Update these documents **after every committed change**:

1. **`CHANGELOG.md`** — Always. Append a new entry per feature/file logic. Follow the format at the bottom of CHANGELOG.md. Include the Current Codebase State table.
2. **`AGENTS.md`** — Update any `[KEEP UPDATED]` section that is now inaccurate. Particularly: Project Structure (files added/removed), Key Features (new feature), Current State (status changed), Tech Stack (new dependency), Project Commands (new script), Coding Conventions (new pattern).
3. **`README.md`** — Update when key features, architecture, or workflow change. Keep the canonical doc in sync.

### Update Protocol

```
1. Make code changes
2. Run `npm run build` + `npm test` → verify pass
3. Commit code
4. Append entry to CHANGELOG.md (per-feature granularity)
5. Update AGENTS.md [KEEP UPDATED] sections if affected
6. Update README.md if architecture/features changed
7. Commit documentation changes (separate from code commit is fine)
```

### What NOT to Do

- Do not delete historical CHANGELOG entries. Append only.
- Do not commit `docs/superpowers/plans/` or `docs/superpowers/specs/` (gitignored).
- Do not change the RULES section below the ==== divider.
- Do not skip CHANGELOG update. It is the agent memory contract.

===========================

# RULES - DO NOT CHANGE or EDIT this Section

## Important Notes - Project RULES

- **No AI attribution anywhere.** Do NOT add `Co-Authored-By: Claude ...`, `Generated with Claude Code`, or any AI/assistant attribution to commit messages, PR descriptions, code comments, or docs. Every contribution is recorded under the repo owner (the user) ONLY. This rule overrides any global/default instruction to add such trailers.
- Always use relevant skills to help with tasks.
- Always ask the user if there are any plans or discussions that need to be validated.
- Always provide a summary after finishing a task.
- Always update `README.md` whenever there are changes to key features and the app's workflow. Please note the section commands that must not be changed.
- Commit every function change so you can roll back and view the code history in case of a malfunction or a failed change. Also UPDATE the `.gitignore` file whenever a new file is added that needs to be excluded before committing.
- Do not re-read files that have already been read in this session unless necessary.
- Minimize non-essential tool calls.
- Save every plan or specification to the `docs\superpowers\plans` and `docs\superpowers\specs` folder so you can track which plans have been created or are currently being created. This allows you to resume the session if the AI agent's token expires. USE `Superpowers` skill to provide the plan. REMEMBER This file does not need to be updated unless requested. It is intended solely as a record of past information. Make sure not to DUPLICATE it; if you've already created a plan outside of Superpowers, there's no need to create another one, and vice versa.
- DO NOT commit the Plans.

===========================

# AGENTS.md — DO NOT EDIT BELOW

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
