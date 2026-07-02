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
2. **`qc_server/`** — Backend server for live detection crop capture, async batch defect segmentation, and interactive SAM point/box annotation. **(Active: M0-M3 + Live Streaming Slices 1-3 + Auto/Manual redesign + raw pending batches + real `sam3_prompt` + SAM click-to-segment; lossless padded PNG crops)**
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
| Testing | Vitest + Vue Test Utils + jsdom | ^4.1 / ^2.4 / ^27 |
| CSS | Vanilla CSS with CSS Variables (no Tailwind, no UI library) | — |
| Design system | Carbon Design System (IBM) with light/dark mode | — |

### Backend (`qc_server/`)

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | SQLite via SQLAlchemy 2.0 |
| Schemas/config | Pydantic v2 + pydantic-settings |
| Image metadata | Pillow |
| Upload parsing | python-multipart |
| Camera streaming | OpenCV headless (`opencv-python-headless`) |
| Object detection/counting | Ultralytics + supervision (server-only `requirements-ml.txt`, lazy imports) |
| Testing | pytest + FastAPI TestClient |
| Defect strategy | Pluggable interface, `mock` and `sam3_prompt` implemented; interactive SAM point/box endpoint |

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

- **Sidebar navigation shell** (collapsible) with 9 pages; Media Detection is always visible. `GSPE | MQC-AI` wordmark that centers `GSPE` when collapsed.
- **Live Monitor**: API-backed camera selector (RaspyCam/RTSP/USB), explicit Start Camera raw preview, per-run Auto/Manual mode, Auto server-annotated MJPEG detection feed with bounding-box/count overlay and presence-cycle best-frame lossless padded PNG crop per object, Manual one-shot Capture, polled live object count/FPS, real online/offline camera status, and Send to QC crop approval gate with batch name + auto-timestamp.
- **QC Studio**: 3-column layout with pending raw image list/canvas before segmentation, batch sidebar (filter/search/sort/skeleton loading), per-image delete with confirmation, Re-run and Reset controls for finished batches, default view-only review/export mode, opt-in edit mode persisted in localStorage, floating canvas tool docks (icon-labeled Select/Draw/SAM point/SAM box/Reshape/Delete, annotation/review/View|Edit, zoom), universal Cancel/Esc for draw/SAM/reshape/class-pick states, bidirectional row/polygon defect selection, cursor-aware pan/draw/SAM/reshape/select states, keyboard shortcuts, SAM point/box assisted defect add, manual polygon defect add fallback, vertex reshape for selected defects, false-positive delete, defect relabel, configured defect-class annotation colors, and defect panel (keyboard navigation, review workflow, whole-batch Export Full/Crop PNG/ZIP with `DefectClass.color`).
- **Batch History**: searchable/filterable table of all processed batches, click to reopen in QC Studio, delete with confirmation.
- **Reports**: PDF audit report generator (batch summary, grouped annotated defect crops, signature/approval fields) via jsPDF.
- **Audit Log**: auto-logged activity trail (all user actions across the app).
- **Settings**: API-backed camera CRUD, grouped "Models" section (object-detection model switcher `active_model`, QC/segmentation model switcher `qc_model`, Quantity Detection model switcher `quantity_model`), separate object-detection, QC, and Quantity confidence thresholds, defect strategy, defect-class management (grouped enable/add/edit/delete/color), save toast, preferences (language, theme).
- **Media Detection**: production upload UI with drag-and-drop staging, multiple-image image mode, explicit Run trigger, active-model strip, per-image Test result cards, combined Process-to-QC crop extraction for all staged images, video Test/Process single-file flow, progress feedback, crop review, approval, and QC batch submission.
- **Quantity Detection** (Phase 1: image): dedicated "Quantity" sidebar group with distinct count/history icons. Quantity Detection page runs the configured Quantity Detection model against one or more uploaded images, shows a selected annotated canvas with returned detection boxes, an image filmstrip, per-image count badges, selected-image object crop evidence, session cumulative total + per-class counts, Pass/Fail verdict against expected total + tolerance, and saves the result (persisted record + per-image `inputs` crop URLs + `QUANTITY_CHECK` audit log entry). Quantity History page lists saved checks with search/filter, CSV export, Inspect combined crop gallery, and Delete confirmation.
- **Bilingual i18n** (Bahasa Indonesia / English) with toggle, persisted in localStorage.
- **Light/Dark mode** toggle (Carbon Gray-100 dark theme), persisted in localStorage.

### Backend (current — `qc_server` M0-M3)

- FastAPI backend under `qc_server/` with `/health`, startup table creation, CORS, and `.env` config.
- SQLite metadata for cameras, defect classes, settings, audit logs, batches, images, defects, and quantity checks.
- CRUD APIs for cameras, defect classes, settings, and audit logs; defect classes have comprehensive coating/welding idempotent seed data and optional auto-generated create IDs.
- OpenCV-backed camera probe + raw MJPEG stream endpoint (`GET /api/cameras/{camera_id}/stream`), one-shot `grab_one()` frame capture helper, annotated/downscaled detection MJPEG endpoint (`GET /api/cameras/{camera_id}/detect-stream`) with Auto presence-cycle counting/cropping for one-at-a-time parts, live count/FPS endpoint (`GET /api/cameras/{camera_id}/count`), per-camera lossless padded PNG crop session capture, and background camera status monitor.
- Count-gate crop endpoints: `POST /api/cameras/{camera_id}/crop-session/start` resets a run, `POST /api/cameras/{camera_id}/capture` appends Manual captures, `POST /api/cameras/{camera_id}/crop-session/finalize` returns lossless padded PNG crop URLs for review, `POST /api/cameras/{camera_id}/crop-session/approve` copies selected crops to the approved batch folder, and `GET /api/cameras/{camera_id}/crops/{session_ts}/{filename}` serves crop thumbnails with inferred content type.
- Media detection upload endpoints: `POST /api/detect/image`, `POST /api/detect/video`, annotated video playback `GET /api/detect/video/{video_id}/stream`, sync multi-image crop export `POST /api/detect/image/process` via multipart `files`, async video crop extraction `POST /api/detect/video/{video_id}/extract`, extraction status `GET /api/detect/video/{video_id}/extract/status`, media crop finalize/approve, and crop serving.
- Quantity Detection (Phase 1: image) endpoints: `POST /api/quantity/detect/image` reuses `object_detection.detect()`/`serialize_detections()` with the dedicated `quantity_model`/`quantity_confidence_threshold` settings (409 if no quantity model configured), writes bbox object crops via `crop_objects()` into `data/quantity/_tmp/<crop_key>/`, returns crop URLs, serves crops through `GET /api/quantity/crops/{p1}/{p2}/{filename}`, and `POST/GET/GET-by-id/DELETE /api/quantity/checks[/{id}]` persist/list/retrieve/delete saved `QuantityCheck` records (total/per-class counts, expected total, tolerance, verdict, per-image `inputs`) while moving temp crops to `data/quantity/<check_id>/<index>/` and deleting crop folders with checks.
- Server-only object detection and SAM 3 dependencies in `requirements-ml.txt`; `qc_server/models/*.pt` files are listed by `/api/models`, Settings persists separate `active_model`, `qc_model`, `quantity_model`, `confidence_threshold`, `qc_confidence_threshold`, and `quantity_confidence_threshold`, and ML imports stay lazy for laptop tests.
- `Setting.input_mode_enabled` guarded migration remains for compatibility; frontend navigation no longer uses it.
- Async batch **defect** segmentation over crop folders via **polling** (`job_id` → poll status), with raw image rows pre-created at submit, re-run allowed for non-processing batches, reset-to-pending/raw endpoint, `DELETE /api/batches/{batch_id}` cleanup for batch records/images/defects/result directories, `DELETE /api/batches/{batch_id}/images/{image_id}` for row + crop-file removal, nested defect `POST/PATCH/DELETE /api/batches/{batch_id}/images/{image_id}/defects[/{defect_id}]` for manual QC corrections, and `POST /api/batches/{batch_id}/images/{image_id}/segment` for interactive SAM point/box polygon generation.
- Pluggable defect strategy interface with deterministic `mock` and real `sam3_prompt` strategies implemented; `sam3_prompt` uses enabled defect-class names as SAM 3 text prompts and a lazy `SAM3SemanticPredictor` seam. Interactive SAM uses lazy Ultralytics `SAM` loading with the configured `qc_model`, point or `bboxes=` prompts, highest-confidence mask selection, and shared polygon simplification.
- Filesystem result output under `qc_server/data/batches/<batch_id>/result.json`, source crops under `qc_server/data/crops/<camera_id>/<session_ts>/` as lossless padded PNG files, and crop/result image serving via `/api/cameras/.../crops/...` and `/api/images/{image_id}/file`.

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
│       │   ├── batches.js           # Batch submit/status/result/list/review/image-delete/delete API
│       │   ├── cameras.js           # Camera CRUD API
│       │   ├── defectClasses.js     # Defect class CRUD API
│       │   ├── detect.js            # Media Detection test/process upload API
│       │   ├── models.js            # Detection model list API
│       │   ├── quantity.js          # Quantity detect-image/checks API (save/list/detail/delete)
│       │   └── settings.js          # Settings API with snake/camel mapping
│       ├── router/
│       │   └── index.js             # 9 named routes
│       ├── assets/
│       │   └── locales/
│       │       ├── id.js            # Indonesian translations (~300 strings)
│       │       └── en.js            # English translations
│       ├── components/
│       │   ├── AppSidebar.vue       # Collapsible grouped nav (9 pages)
│       │   ├── TopBar.vue           # Slim top bar (title, theme, i18n, profile)
│       │   ├── BatchSidebar.vue     # Batch list with filter/search/review progress
│       │   ├── InspectionCanvas.vue # Image canvas with zoom/pan/annotation
│       │   ├── DefectClassModal.vue # Defect class add/edit modal
│       │   ├── DefectPanel.vue      # Defect details + export + keyboard nav
│       │   └── CropReviewDialog.vue # Shared crop approval dialog
│       ├── composables/
│       │   ├── useTheme.js          # Light/dark theme toggle (localStorage)
│       │   ├── useI18n.js           # ID/EN language toggle (localStorage)
│       │   ├── useInspection.js     # Batch loading, image selection, review workflow
│       │   ├── useCameras.js        # Camera CRUD (live API)
│       │   ├── useBatchHistory.js   # Batch history list/delete (live API)
│       │   ├── useAuditLog.js       # Audit trail logging (live API + local cache)
│       │   ├── useDefectClasses.js  # Defect class CRUD state (live API)
│       │   ├── useDefectColor.js    # Defect class color lookup for QC annotations
│       │   ├── useSettings.js       # Object/QC/Quantity model + confidence config + defect strategy + legacy input mode mapping (live API)
│       │   ├── useQuantityHistory.js # Saved quantity-check list/delete (live API)
│       │   └── useToast.js          # App-wide transient toast message
│       ├── views/
│       │   ├── LiveMonitor.vue      # Camera selector + detection + send-to-QC
│       │   ├── QCStudio.vue         # 3-column inspection studio
│       │   ├── BatchHistory.vue     # Batch table with search/filter
│       │   ├── MediaDetection.vue   # Production image/video upload, Test, and Process-to-QC crop flow
│       │   ├── QuantityDetection.vue # Quantity count/verify (annotated canvas + filmstrip + crop evidence)
│       │   ├── QuantityHistory.vue  # Saved quantity checks (search/filter + CSV export + combined crop inspect/delete)
│       │   ├── Reports.vue          # PDF report generator
│       │   ├── AuditLog.vue         # Activity log table
│       │   ├── Settings.vue         # Camera CRUD + object/QC model config + defect classes + preferences
│       │   └── __tests__/           # Vue component tests
│       └── utils/
│           ├── canvasCoords.js      # toImageCoords SVG pointer-to-image coordinate helper
│           ├── defect.js            # polygonBBox helper (color comes from useDefectColor)
│           ├── export.js            # Canvas render + whole-batch crop/full export (injected colorFor)
│           ├── quantity.js          # Pure count/verdict/CSV helpers (perClassFromDetections, addCounts, totalOf, computeVerdict, checksToCsv)
│           └── mockData.js          # Seed data (3 cameras, 5 batches, 15 logs)
├── qc_server/                # FastAPI backend (M0-M3 done, mock + sam3_prompt strategies)
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
│   │   │   ├── cameras.py           # Camera CRUD, stream/count, crop start/capture/finalize/approve
│   │   │   ├── defect_classes.py
│   │   │   ├── detect.py            # Media Detection image/video upload/process endpoints
│   │   │   ├── images.py
│   │   │   ├── models.py            # GET /api/models
│   │   │   ├── quantity.py          # Quantity detect-image + checks save/list/detail/delete
│   │   │   └── settings.py
│   │   └── services/
│   │       ├── camera_monitor.py    # Background camera reachability polling
│   │       ├── counting.py          # Pure single/tracking object count helpers
│   │       ├── crop.py              # Bbox crop writer helper
│   │       ├── crop_session.py      # Shared crop session registry
│   │       ├── detect_extract.py    # Uploaded-video crop extraction job
│   │       ├── presence_counter.py  # Auto one-at-a-time presence-cycle crop counter
│   │       ├── annotated_stream.py  # Server-side annotated detection MJPEG
│   │       ├── job_queue.py
│   │       ├── pipeline.py
│   │       ├── quantity.py          # per_class_counts(detections) grouping helper
│   │       ├── seed.py
│   │       ├── detect_tracker.py    # Lazy supervision tracking helper
│   │       ├── frame_grabber.py     # Threaded latest-frame camera reader
│   │       ├── object_detection.py  # Lazy YOLO object detection + serialization
│   │       ├── streaming.py         # OpenCV RTSP/USB probe + MJPEG frame generator + grab_one
│   │       └── inference/
│   │           ├── __init__.py      # Lazy YOLO object detection + serialization
│   │           ├── base.py
│   │           ├── mock.py
│   │           ├── sam3.py           # Lazy SAM 3 prompt strategy + polygon simplifier
│   │           └── sam_interactive.py # Lazy SAM point/box interactive segmentation
│   └── tests/
├── edge_app/                 # Jetson Nano edge app (not yet started)
├── docs/
│   ├── PRD.md                # Product Requirements Document
│   ├── workflow.md           # System workflow + architecture diagram
│   └── superpowers/
│       └── plans/            # Implementation plans (gitignored, not committed)
├── DESIGN.md                 # Carbon Design System spec (light/dark tokens)
├── PRODUCT.md                # Product/register context for design work
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

- Source of truth: `DefectClass.color` (configured in Settings), resolved via `useDefectColor().colorFor(type)`.
- Canvas rendering (`InspectionCanvas.vue`), panel swatches/report tags (`DefectPanel.vue`, `Reports.vue`), and PNG export (`utils/export.js` `renderAnnotated(imgEl, image, colorFor)`) all take the same `colorFor` resolver, so on-screen and exported colors always match.
- `utils/defect.js` only provides `polygonBBox`; there is no separate CSS-variable color map.

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
    → [Start Camera raw preview]
    → [Auto: Start/Stop Detection + Presence Count/FPS + Best-Frame Crops | Manual: Capture x N]
    → [Optional Media Detection: stage upload(s) → Run Test preview or Process media crops to QC]
    → [Review & Send: finalize crop session + approve crop grid + batch name]
    → [QC Studio: pending RAW image list/canvas + optional image delete]
    → [SAM3 Batch Processing (backend)]
    → [QC Studio: View-only review/export OR Edit mode floating tools + row/polygon selection + SAM point/box or manual add/delete/reshape/relabel + zoom/pan + mark reviewed + optional re-run/reset]
    → [Export: Crop/Full PNG + PDF Audit Report with annotated defect crops]
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

### Status: SAM Click-to-Segment Implemented · Backend M0-M3 Implemented

**What is developed now**: Frontend dashboard data is now backed by the live `qc_server` API for cameras, settings, defect classes, batches, reports, audit log, and QC Studio flow. Live Monitor has an explicit Start Camera raw preview, per-run Auto/Manual choice, Auto server-annotated MJPEG detection frames/boxes/count overlay with presence-cycle best-frame cropping for one-at-a-time parts, Manual one-shot Capture, `/count` polling for count + FPS, and a shared Review & Send crop approval dialog before submitting a QC batch. QC Studio can open pending batches as raw image rows/canvas before segmentation, delete an image and underlying crop file, run/re-run SAM 3/QC with dedicated QC confidence, reset a finished batch back to pending/raw, color polygons/panel swatches from Settings defect-class colors, and opt into persisted edit mode with icon-labeled floating canvas tool docks, universal Cancel/Esc for draw/SAM/reshape/class-pick states, bidirectional defect row/polygon selection, cursor-aware pan/draw/SAM/reshape/select feedback, keyboard shortcuts, SAM point/box assisted defect polygon generation, manual defect polygon drawing fallback, vertex reshape for selected defect boundaries, false-positive delete, or defect relabel; view-only remains the default. Reports PDFs include grouped, annotated per-defect crop images while preserving vector text for report copy/signature fields. Settings lists `.pt` files from `qc_server/models/`, groups the three model selectors under a "Models" heading as model/confidence pairs, and persists separate `active_model` (object detection), `qc_model` (QC segmentation), `quantity_model` (Quantity Detection), object-detection confidence, QC confidence, and Quantity confidence, saves defect strategy, manages grouped coating/welding defect classes with enable/add/edit/delete/color, and confirms saves with a toast. Media Detection is always visible and stages uploaded images/videos before an explicit Run action; image mode supports multiple staged images with per-image Test cards and combined Process-to-QC crop extraction into one review/submitted batch, while video remains single-file. A dedicated **Quantity** sidebar group (Phase 1: image input) holds Quantity Detection — multi-image upload with a selected annotated canvas, image filmstrip, returned detection-box overlays, per-image count badges, selected-image object crop evidence, session-cumulative total + per-class counts, source selector with Video/Camera disabled for Phase 2, no-model Settings link, optional expected-total + tolerance Pass/Fail result band, Save toast (persists a `QuantityCheck` record with permanent per-image crop URLs in `inputs` and logs a `QUANTITY_CHECK` audit entry) — and Quantity History, a searchable/filterable list of saved checks with CSV export, Inspect combined crop gallery, and Delete confirmation; video/camera input and per-class expected targets are Phase 2/deferred UI (the data model already carries `source_type`/`count_mode`). **Backend (`qc_server`) M0-M3 plus Live Streaming Slices 1-3, the Auto/Manual redesign, Auto presence-cycle crop, Media Detection crop-to-QC, lossless padded PNG crop output, raw pending batch rows, image row/file delete, nested defect CRUD for manual corrections, interactive SAM segment endpoint, batch re-run/reset, defect-class management, real `sam3_prompt` strategy, and Quantity Detection Phase 1 are implemented**: FastAPI + SQLite metadata APIs, async batch pipeline, mock and SAM 3 prompt defect strategies, lazy SAM point/box segmentation using `qc_model`, comprehensive idempotent defect-class seed data, optional auto-generated defect-class create IDs, result JSON, crop image serving, OpenCV raw/annotated MJPEG streaming, latest-frame grabber, one-shot capture, crop approval endpoints, stream downscale/FPS cap, model-folder switcher, media detection upload/process endpoints including multi-image process sessions, per-camera/media crop sessions, shared `crop_objects()` PNG writer with ~5% bbox padding, background camera status monitoring, and quantity detect-image/checks endpoints reusing the existing YOLO `detect()` with check save/list/detail/delete plus temp/permanent object crop evidence storage. Real-weight SAM 3 GPU smoke remains pending. Quantity Detection browser smoke also remains pending (needs a real detection `.pt` set as the Quantity model in Settings).

### Component Status

| Component | Status | Description |
|---|---|---|
| `qc_frontend/` | **Active** | 9 pages, Carbon Design System, i18n, live API-backed data, Auto/Manual Live Monitor, annotated MJPEG detection feed/count/FPS, Auto presence-cycle crop results, shared Send-to-QC crop approval gate, pending raw QC images, image delete, view/edit QC defect correction with SAM point/box, reshape, and manual tools, re-run/reset controls, object/QC/Quantity model and confidence split, defect-class management/colors, production Media Detection upload Test/Process modes with multi-image image staging, Quantity Detection annotated canvas/filmstrip/crop evidence + Quantity History with CSV export, combined crop inspect, and delete. |
| `qc_server/` | **Active** | FastAPI + SQLite backend. M0-M3 + Live Streaming Slices 1-3 + Auto/Manual redesign + Auto presence-cycle crop + Media Detection crop-to-QC including multi-image process sessions + raw pending batch rows + image row/file delete + nested defect CRUD + interactive SAM segment endpoint + re-run/reset + lossless padded PNG crop output + defect-class seed/API + `sam3_prompt` strategy + Quantity Detection Phase 1 (detect-image + temp/permanent crop evidence + checks save/list/detail/delete with `inputs`) done; GPU smoke pending. |
| `edge_app/` | **Not started** | Jetson Nano YOLO detection + live streaming. Planned. |

### Frontend Page Status

| Page | Status | Mock Data | Backend Ready |
|---|---|---|---|
| Live Monitor | **Functional** | None for camera feed/counting | Camera list, Start Camera raw preview, Auto presence-cycle detection/crop stream, Manual capture, `/count` count/FPS polling, real status, lossless padded PNG crop-session finalize/approve review gate, and Send to QC API wired |
| QC Studio | **Functional** | None for live batches | Pending raw image list/canvas, image delete, view-only default, persisted edit mode with icon-labeled floating tools and universal Cancel/Esc, bidirectional row/polygon selection, cursor-aware draw/SAM/reshape/select/pan states, shortcuts, SAM point/box assisted add, manual polygon add/delete/relabel, selected-defect vertex reshape, re-run/reset controls, batch polling/result/review/sign-off API wired; configured class colors; `sam3_prompt` and interactive SAM endpoint implemented for configured SAM 3 weights |
| Batch History | **Functional** | None | Live batch list and delete APIs wired |
| Media Detection | **Functional** | None | Always-visible production upload UI with drag/drop staging, explicit Run trigger, multi-image image Test cards via `/api/detect/image`, Process image sync lossless padded PNG crop across all staged images via one `/api/detect/image/process` session, Process video async presence-cycle crop extraction, crop approval, and QC batch submission wired; browser smoke pending |
| Reports | **Functional** | None | Live batch/result API wired; PDFs include grouped annotated defect crops |
| Audit Log | **Functional** | Local cache fallback | Live audit API wired |
| Settings | **Functional** | None | Camera CRUD, settings API, grouped "Models" section (object detection / QC-segmentation / Quantity Detection model switchers), separate object/QC/Quantity confidence, defect strategy, grouped defect-class enable/add/edit/delete/color, preferences, and save toast wired |
| Quantity Detection | **Functional** (Phase 1: image) | None | Multi-image upload via `/api/quantity/detect/image`, selected annotated canvas, filmstrip switching, returned detection-box overlays, per-image count badges, selected-image crop evidence, session-cumulative total + per-class counts, expected-total + tolerance Pass/Fail result band, no-model Settings link, Save toast via `/api/quantity/checks` + `QUANTITY_CHECK` audit log wired; requires a Quantity Detection model configured in Settings |
| Quantity History | **Functional** | None | Live `/api/quantity/checks` list, search/filter, CSV export, Inspect dialog with combined crop gallery from persisted `inputs[].crops`, and Delete via `/api/quantity/checks/{id}` wired |

### Detailed Log

See [`CHANGELOG.md`](./CHANGELOG.md) for the comprehensive, per-feature change log with Current Codebase State tables.

**Latest version**: [Unreleased] - 2026-07-02 (Quantity Inference Display + Crop Evidence; Quantity Detection UX v2; Quantity Detection Phase 1 (Image); QC Studio Vertex Reshape Tool; Config Storage Path Anchoring; QC Studio Edit Dock Cancel and Labels; QC Studio SAM Click-to-Segment; QC Studio Edit-Mode UX; QC Studio Manual Defect Editing; Audit Report PDF Defect Crops; Media Detection Multi-Image Upload; QC Studio Batch Export).

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
