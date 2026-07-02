# MQC-AI (Manufacturing Quality Control AI)

## Project Overview

MQC-AI adalah sistem inspeksi kualitas produk berbasis *Computer Vision* end-to-end yang dirancang untuk otomasi deteksi cacat di lini produksi industri (misal: pelapisan/coating dan pengelasan). Proyek ini merupakan inisiatif untuk GSPE.

Sistem ini menggunakan arsitektur *decoupled* yang dipisahkan menjadi 3 komponen utama, namun dikelola dalam satu *repository* (monorepo). Inspector memantau live feed dari kamera, trigger pengiriman batch ke server SAM3 untuk analisis, lalu me-review hasil segmentasi cacat dan generate laporan audit.

## Arsitektur & Workspace

| Component | Status | Description |
|---|---|---|
| `qc_frontend/` | **Active** | Vue 3 dashboard dengan 9 halaman, Carbon Design System, i18n bilingual, live `qc_server` API integration, Auto/Manual Live Monitor, annotated MJPEG detection feed/count/FPS, Auto presence-cycle crop results, shared Send-to-QC crop approval gate, pending raw QC images, image delete, QC Studio view/edit defect correction with icon-labeled floating edit tools, universal Cancel/Esc, SAM point/box assisted annotation, selected-defect vertex reshape, and linked row/polygon selection, re-run/reset controls, Settings object/QC/Quantity model and confidence split, Settings defect-class management/colors, production Media Detection Test/Process upload page with multi-image image mode, Quantity Detection annotated canvas/filmstrip/crop evidence view, and Quantity History combined crop inspect/delete |
| `qc_server/` | **Active (M0-M3 + streaming slices 1-3 + Auto/Manual redesign + Auto presence-cycle crop + Media Detection crop-to-QC + raw pending batches + manual defect CRUD + interactive SAM + re-run/reset + defect-class management + SAM3 prompt + Quantity Detection)** | FastAPI + SQLite backend untuk async batch **defect** segmentation, raw image rows at submit, image row/file delete, nested manual defect CRUD, SAM point/box segmentation endpoint, batch re-run/reset, comprehensive idempotent defect-class seed/API, `mock` and real `sam3_prompt` defect strategies, CRUD metadata APIs, RTSP/USB camera streaming, annotated MJPEG detection/counting/FPS, one-shot capture, Auto presence-cycle best-frame lossless PNG crops with padding, per-camera/media crop sessions, crop approval endpoints, sample image/video test endpoints, multi-image media crop-to-QC endpoints, Quantity detect-image temp crops and checks save/list/detail/delete with persisted crop evidence, real camera status monitor |
| `edge_app/` | Planned (after server) | Jetson Nano + TensorRT/`supervision` untuk **deteksi & penghitungan objek produk** + count-approval gate + live streaming |

### End-to-End Workflow

```
[Live Monitor] Start Camera raw preview
    → [Auto: Start/Stop Detection presence-cycle best-frame crop | Manual: Capture x N]
    → [Review & approve crop grid]
    → [Trigger: POST /api/batches dengan approved crop folder]
    OR [Media Detection] Stage upload(s) -> Run Test preview / Process uploaded media to crop review
    OR [Quantity Detection] Add images -> annotated canvas + filmstrip + crop evidence -> verify total verdict -> save check with persisted crop URLs
    → [QC Studio: pending RAW image list/canvas + optional image delete]
    → [qc_server: async defect segmentation (mock or SAM3 prompt), polling]
    → [QC Studio: View-only review/export OR Edit mode floating tools + row/polygon selection + SAM point/box or manual add/delete/reshape/relabel + zoom/pan + mark reviewed + optional re-run/reset]
    → [Export: Crop/Full PNG + PDF Audit Report with annotated defect crops]
    → [Audit Log: auto-trails all actions]
```

Detail: [`docs/workflow.md`](./docs/workflow.md) | [`docs/PRD.md`](./docs/PRD.md)

> **Phase C-3 integration note:** The dashboard now uses the live `qc_server` API for QC Studio, Live Monitor's "Send to QC", Batch History, Reports, Audit Log, Cameras, Defect Classes, and Settings via the Vite dev proxy (`/api` → `http://localhost:8787`, same-origin, no CORS). Settings now persists model configuration, separate object-detection and QC confidence thresholds, `defect_strategy`, and separate `active_model` / `qc_model` selections to `/api/settings`, and manages enabled defect classes/colors through `/api/defect-classes`.
>
> **Live Streaming Slice 2.3:** Live Monitor consumes annotated MJPEG from `GET /api/cameras/{id}/detect-stream`; the browser renders it as an `<img>`, while the metric strip polls `GET /api/cameras/{id}/count` for `{ count, fps }`. The detection stream downscales before inference and caps loop FPS via `MQC_STREAM_MAX_WIDTH` / `MQC_STREAM_MAX_FPS` (defaults: `960` / `15`). `GET /api/cameras/{id}/stream` remains available as the raw MJPEG fallback. Drop YOLO `.pt` weights into `qc_server/models/`, then choose the active file in **Settings -> Model Configuration -> Object Detection Model**. Object detection uses server-only ML deps in `qc_server/requirements-ml.txt`.
>
> **Live Monitor Auto/Manual Flow:** Start Camera resets a per-camera crop session and shows raw MJPEG preview. Auto runs `GET /api/cameras/{id}/detect-stream` until Stop Detection and uses presence debounce to count/crop one best frame per object, suited to workers presenting parts one at a time without relying on ByteTrack. Manual calls `POST /api/cameras/{id}/capture` per click. Review & Send calls `POST /api/cameras/{id}/crop-session/finalize`, lets the operator check selected lossless padded PNG crop thumbnails, then calls `POST /api/cameras/{id}/crop-session/approve` and submits `POST /api/batches` with the approved crop folder.
>
> **Media Detection Crop-to-QC:** `/media-detection` is always visible in the sidebar. The page stages image/video uploads with drag-and-drop, shows the active model and confidence threshold, and waits for an explicit **Run detection** action before calling the server. Image mode supports multiple staged images; Test mode uploads each image to `POST /api/detect/image` for separate annotated base64 result cards and detection lists with confidence bars. Video Test uploads one video to `POST /api/detect/video` and plays `GET /api/detect/video/{id}/stream` as annotated MJPEG. Process image mode sends all staged images to `POST /api/detect/image/process` as multipart `files`, collecting immediate object crops into one crop-review dialog and one submitted QC batch; uploaded videos still use `POST /api/detect/video/{id}/extract` with polling via `GET /api/detect/video/{id}/extract/status`. Crop review uses `GET /api/detect/crop-session/{key}`, selected approval uses `POST /api/detect/crop-session/{key}/approve`, then the approved folder is submitted to QC. Uploaded videos are stored under `qc_server/data/uploads/`, which stays gitignored. Browser smoke is deferred to review.
>
> **Quantity Detection Inference Display:** The dedicated Quantity group includes `/quantity` and `/quantity/history`. Quantity Detection uses the configured Quantity Detection model (`quantity_model`) and confidence threshold, draws returned boxes on a selected image canvas, provides a filmstrip to switch uploaded images, shows selected-image object crop evidence generated by the backend, accumulates a big session total + per-class tally, compares against labeled Expected total/Tolerance inputs, and saves checks with permanent per-image crop URLs plus a `QUANTITY_CHECK` audit log. Quantity History lists saved checks, exports CSV, opens Inspect for a combined crop gallery, and deletes checks plus their crop folders through `DELETE /api/quantity/checks/{id}`. Browser smoke needs a real `.pt` selected as the Quantity model.
>
> **Defect Class Management:** Settings includes a compact **Defect Classes** section grouped by Coating and Welding. Operators can enable/disable classes, add classes without hand-writing IDs, edit name/category/color, and delete obsolete classes. The backend seeds 25 canonical coating+welding variants idempotently, so existing databases gain missing classes without overwriting user edits. This is the configuration layer for SAM 3 prompt-based inference in Part B.
>
> **SAM 3 Prompt Strategy:** Batch QC can use `defect_strategy="sam3_prompt"` with a separate **QC / Segmentation Model** (`qc_model`) selected in Settings. The strategy lazily loads Ultralytics `SAM3SemanticPredictor`, embeds each crop once, queries each enabled defect-class name as a text prompt, filters by confidence, simplifies returned mask polygons in pure Python, and stores QC Studio-compatible defect polygons. GPU real-weight smoke remains a reviewer/local-server step.
>
> **QC Workflow Raw/Delete/Colors/Re-run:** `POST /api/batches` now pre-creates pending raw image rows. QC Studio opens pending batches with the same image list and canvas used after segmentation, but without polygons. Inspectors can delete a bad crop from the list via `DELETE /api/batches/{id}/images/{image_id}`, which removes the row and source crop file. Segmentation uses dedicated **QC Confidence**, while object detection keeps **Object Detection Confidence**. QC polygons and DefectPanel swatches use `DefectClass.color` from Settings. Finished batches can be re-run through the same Load Batch dialog, or reset to pending/raw via `POST /api/batches/{id}/reset`.
>
> **QC Studio Manual Defect Editing:** QC Studio defaults to view-only mode for browsing, review, and export. Inspectors can opt into persisted **Edit mode** (`localStorage` key `mqc-edit-mode`) to draw manual defect polygons, choose an enabled defect class, delete false positives, or relabel defects. The backend stores these through nested `POST/PATCH/DELETE /api/batches/{id}/images/{image_id}/defects[/{defect_id}]`, recomputing image status and batch defect counts without changing `image.reviewed`. Manual draw remains the fallback annotation path.

> **QC Studio Edit-Mode UX:** Edit mode now uses floating canvas controls: a left icon-labeled Select/Draw/SAM point/SAM box/Reshape/Delete dock, a top-right annotation/review/View|Edit cluster, and a bottom-right zoom cluster. Universal Cancel/Esc exits manual drawing, SAM tools, SAM box drags, reshape drags, and pending class selection. Defect row and polygon selection are bidirectional in View and Edit modes, selected polygons/rows get stronger active styling, cursors reflect draw/SAM/reshape/pan/select state, and V/A/Delete/Esc/+/-/0 shortcuts cover common actions while ignoring form fields.
>
> **QC Studio Vertex Reshape:** Edit mode includes a Reshape tool for selected defects. It renders SVG handles on every polygon vertex, updates the boundary live while dragging, ignores press-without-move nudges, reverts the active vertex on Esc, and persists only `{ polygon }` through the existing defect PATCH endpoint.
>
> **QC Studio SAM Click-to-Segment:** Edit mode includes SAM point and SAM box tools. `POST /api/batches/{id}/images/{image_id}/segment` runs the configured `qc_model` with a point or `bboxes=` prompt, chooses the highest-confidence mask, simplifies it, and returns a polygon. The frontend feeds that polygon into the existing class picker and saves through the same manual defect POST endpoint. Real point/box quality and latency smoke are deferred to the GPU reviewer.
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

### Pages (9 routes)

| Route | Page | Description |
|---|---|---|
| `/live` | **Live Monitor** | Camera selector (RaspyCam/RTSP/USB), Start Camera raw preview, Auto annotated MJPEG detection with presence-cycle best-frame crop, Manual capture, live object count/FPS, real online/offline status, Send to QC crop approval dialog |
| `/qc` | **QC Studio** | 3-column inspection: pending raw image list/canvas, per-image delete, view-only default, persisted edit mode with icon-labeled floating Select/Draw/SAM point/SAM box/Reshape/Delete tools and universal Cancel/Esc, bidirectional row/polygon selection, cursor-aware draw/SAM/reshape/select/pan states, SAM-assisted or manual polygon add/delete/reshape/relabel, re-run/reset controls, batch sidebar (filter/search) + canvas (zoom/pan) + defect panel (keyboard nav, review workflow) |
| `/batches` | **Batch History** | Searchable table of all processed batches, filter by status, delete with confirmation |
| `/media-detection` | **Media Detection** | Always-visible production upload page with drag/drop staging, multiple-image image mode, explicit Run trigger, Test preview, and Process-to-QC crop export for images/videos |
| `/quantity` | **Quantity Detection** | Multi-image quantity count/verify workflow with selected annotated canvas, image filmstrip, returned detection-box overlays, per-image count badges, selected-image crop evidence, result band total/verdict, expected-total/tolerance target inputs, and Save toast |
| `/quantity/history` | **Quantity History** | Saved QuantityCheck records with search/filter, CSV export, combined crop Inspect dialog, and Delete confirmation |
| `/reports` | **Reports** | PDF audit report generator with summary, grouped annotated defect crops, approval fields |
| `/audit` | **Audit Log** | Auto-logged activity trail, filterable by action type |
| `/settings` | **Settings** | Camera CRUD, object-detection model switcher, QC/segmentation model switcher, Quantity Detection model switcher, paired object/QC/Quantity confidence fields, defect strategy, grouped defect-class enable/add/edit/delete/color, language/theme preferences |

### Key Features

- **Bilingual i18n** (Bahasa Indonesia / English) dengan toggle, persisted di localStorage
- **Light/Dark mode toggle** dengan Carbon Gray-100 dark theme, persisted di localStorage
- **Collapsible sidebar navigation** dengan 9 pages and a refined `GSPE | MQC-AI` wordmark (centered `GSPE` when collapsed)
- **Batch History delete**: batches can be deleted from the dashboard after a confirmation modal via `DELETE /api/batches/{id}`
- **Pending raw QC batches**: submitted batches pre-create raw image rows so QC Studio shows the image list and canvas before segmentation
- **QC Studio image delete**: bad crops can be removed from a batch and from disk via per-image delete before/after loading
- **QC Studio manual + SAM defect editing**: view-only by default; edit mode enables icon-labeled floating Select/Draw/SAM point/SAM box/Reshape/Delete tools, universal Cancel/Esc, bidirectional row/polygon selection, SAM-assisted or manual polygon defects, vertex reshape, false-positive delete, class relabel, and cursor/keyboard support with audit trail
- **QC Studio re-run/reset**: finished batches can be re-segmented or reset to pending/raw while clearing stale reviewed marks
- **Review workflow**: mark/unmark reviewed per image, progress bar, keyboard navigation
- **Zoom/Pan canvas**: mouse wheel zoom (50%-500%), drag to pan, annotation toggle
- **Live API-backed data**: cameras, settings, batches, reports, and audit logs load from `qc_server`; Live Monitor streams raw/annotated MJPEG frames, shows real camera status, and sends approved crop folders to QC
- **Live detection/counting/FPS**: object boxes and count overlay are drawn server-side in Auto via `GET /api/cameras/{id}/detect-stream`; Auto uses presence debounce to count/crop one best frame per physical object; the UI polls `GET /api/cameras/{id}/count` for count and real stream FPS; Manual uses one-shot `POST /api/cameras/{id}/capture`
- **Count-gate crop approval**: `POST /api/cameras/{id}/crop-session/finalize` prepares server-side lossless padded PNG object crops, `POST /api/cameras/{id}/crop-session/approve` copies selected crops, and Send to QC submits only the approved folder
- **Media Detection page**: always-visible upload workspace with drag/drop staging, multi-image image mode, active-model context, explicit Run trigger, invalid/no-model/error states, Test mode annotated result cards, and Process mode image/video lossless padded PNG object crops for shared review and QC batch submission
- **Model switchers**: `.pt` files in `qc_server/models/` are listed by `GET /api/models`; Settings persists `active_model` for live object detection, `qc_model` for batch QC segmentation, and `quantity_model` for Quantity Detection, with separate object/QC/Quantity confidence shown as decimal `0.00-1.00`
- **Quantity Detection**: dedicated count/verify workflow overlays returned YOLO boxes on a selected uploaded image, provides filmstrip switching, shows selected-image object crop evidence, accumulates session total/per-class counts, computes Pass/Fail against Expected total + Tolerance, saves per-image `inputs` with permanent crop URLs, and provides Quantity History search/filter/CSV/combined-crop Inspect/Delete.
- **SAM 3 prompt QC strategy**: `sam3_prompt` uses enabled defect-class names as SAM 3 text prompts and writes confidence-filtered polygons for QC Studio
- **SAM click-to-segment**: QC Studio edit mode calls `POST /api/batches/{id}/images/{image_id}/segment` for point/box prompts, then saves the returned polygon through the existing defect add flow
- **Defect class management**: Settings groups coating/welding defect classes with on/total counts, enable toggles, add/edit/delete, API-backed persistence, and auto-generated IDs for new classes
- **Dynamic defect colors**: QC polygons and DefectPanel swatches use the configured `DefectClass.color` values from Settings
- **Audit report PDF crops**: Reports PDFs keep text as vector jsPDF text and embed grouped annotated defect crops using the same class colors as QC Studio/export

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
- **Ultralytics + supervision** for server-side object detection/counting and SAM 3 prompt segmentation, installed separately from `requirements-ml.txt`
- **pytest** + FastAPI TestClient

### Commands

| Command | Description |
|---|---|
| `cd qc_server && python -m venv .venv` | Create backend virtualenv |
| `cd qc_server && .\.venv\Scripts\python.exe -m pip install -r requirements.txt` | Install backend dependencies |
| `cd qc_server && .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8787` | Start backend API |
| `cd qc_server && .\.venv\Scripts\python.exe -m pytest -v` | Run backend tests |

### Current Scope

Implemented M0-M3 plus Live Streaming Slices 1-3, the Auto/Manual redesign, Auto presence-cycle crop, Media Detection crop-to-QC, Quantity Detection Phase 1, batch deletion, raw pending batch rows, image row/file delete, nested manual defect CRUD, interactive SAM point/box segmentation, batch re-run/reset, defect-class management, real `sam3_prompt` QC strategy, dedicated QC confidence, and lossless padded PNG crop output: health/startup, SQLite schema, seeded cameras/defect classes/settings, comprehensive coating+welding idempotent defect-class seed data, optional auto-generated defect-class create IDs, metadata CRUD, audit log, async batch polling, `DELETE /api/batches/{id}` cleanup, `DELETE /api/batches/{id}/images/{image_id}` row + crop-file cleanup, `POST/PATCH/DELETE /api/batches/{id}/images/{image_id}/defects[/{defect_id}]` manual corrections, `POST /api/batches/{id}/images/{image_id}/segment` point/box SAM polygon generation, `POST /api/batches/{id}/reset`, deterministic `mock` defect strategy, Ultralytics SAM 3 text-prompt defect strategy, `result.json` output, crop image serving, `GET /api/cameras/{id}/stream` raw MJPEG streaming, `GET /api/cameras/{id}/detect-stream` annotated MJPEG detection/counting stream with downscale/FPS cap and presence-cycle best-frame crop, `GET /api/cameras/{id}/count` returning count and FPS, one-shot `grab_one()` capture, per-camera/media crop sessions, `POST /api/cameras/{id}/crop-session/start`, `POST /api/cameras/{id}/capture`, `POST /api/cameras/{id}/crop-session/finalize`, `POST /api/cameras/{id}/crop-session/approve`, camera/media crop thumbnail serving with inferred content type, `/api/detect/*` sample image/video detection endpoints, multi-image image process crop export, async video crop extraction/status polling, media crop approval, `POST /api/quantity/detect/image` with temp object crop evidence, `GET /api/quantity/crops/{p1}/{p2}/{filename}`, `POST/GET/GET-by-id/DELETE /api/quantity/checks[/{id}]` with per-image `inputs` and permanent crop URLs, and background camera status monitoring. Real-weight SAM 3 GPU smoke is pending.

Detection stream performance is configured with `MQC_STREAM_MAX_WIDTH` (default `960`) and `MQC_STREAM_MAX_FPS` (default `15`). Downscaling happens before detection so drawn boxes match the streamed frame.

Crop sessions store source images under `qc_server/data/crops/<camera_id>/<session_ts>/` as `obj_NNN.png`. Start Camera resets the session; Auto detection appends one lossless PNG best-frame crop per debounced presence cycle and Manual Capture appends one-shot crops. Each crop uses about 5% bbox padding, clamped to the original frame, so fine defect texture stays lossless and edge defects keep context. Stop Detection leaves the buffer available for Review & Send; approved copies go under `approved/`.

Media Detection uploads require `python-multipart`. Test images return annotated JPEG data and serialized detections; the frontend can run this once per staged image. Test videos are saved to `qc_server/data/uploads/` and streamed back as annotated MJPEG using the active model. Process images post multipart `files` and crop detected objects from every valid image into one synchronous lossless padded PNG crop session; Process videos run a background presence-cycle extraction job and expose crop review/approval endpoints before QC batch submission.

Server-only detection dependencies are kept out of the laptop/base install. On the GPU server, install a CUDA-matched `torch` first, then `cd qc_server && .venv/bin/python -m pip install -r requirements-ml.txt`, copy `.pt` weights into `qc_server/models/`, choose **Object Detection Model** for live streams and **QC / Segmentation Model** for SAM 3 batches in Settings, and run the backend.

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
| [`PRODUCT.md`](./PRODUCT.md) | Product/register context for design work |
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
- `2026-06-29-detection-test-page.md` - Original upload test page with image/video upload and server setting gate
- `2026-06-29-live-streaming-slice3-count-gate-crop-qc.md` - Count-gate crop capture and Send-to-QC review flow
- `2026-06-29-live-monitor-auto-manual-flow.md` - Live Monitor Start Camera, Auto/Manual, capture, and crop approval redesign
- `2026-06-29-media-detection-crop-to-qc.md` - Media Detection Test/Process modes with crop-to-QC flow
- `2026-06-30-media-detection-upload-ui.md` - Media Detection production upload UI with drag/drop staging and explicit Run trigger
- `2026-06-30-defect-class-management.md` - Comprehensive defect-class seed plus Settings management UI for SAM 3 MVP Part A
- `2026-06-30-sam3-strategy.md` - SAM 3 MVP Part B `sam3_prompt` strategy and QC model split
- `2026-06-30-qc-workflow-raw-delete-colors.md` - QC Studio raw pending images, image delete, QC confidence split, configured defect colors, and re-run/reset workflow
- `2026-07-01-media-multi-image.md` - Media Detection multiple-image upload, per-image Test cards, and combined Process-to-QC image crop sessions
- `2026-07-01-qc-defect-editing.md` - QC Studio view/edit mode with manual defect add/delete/relabel
- `2026-07-01-qc-edit-ux.md` - QC Studio floating edit tools, linked defect selection, cursor helper, drawing hint, and shortcuts
- `2026-07-01-qc-sam-segment.md` - QC Studio SAM point/box assisted annotation backed by an interactive segment endpoint
- `2026-07-02-qc-vertex-reshape.md` - QC Studio Reshape tool for dragging selected defect polygon vertices
- `2026-07-02-quantity-ux-v2.md` - Quantity Detection annotated result dashboard, Settings/nav quick wins, and Quantity History inspect/delete
- `2026-07-02-quantity-inference-display.md` - Quantity Detection selected canvas, filmstrip, crop evidence, persisted crops, and combined History Inspect gallery

---
*Dokumen ini harus selalu diperbarui setiap kali ada penambahan fitur utama atau perubahan arsitektur. Lihat protocol di `AGENTS.md` > Documentation Maintenance.*
