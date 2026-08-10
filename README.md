# MQC-AI (Manufacturing Quality Control AI)

## Project Overview

MQC-AI adalah sistem inspeksi kualitas produk berbasis *Computer Vision* end-to-end yang dirancang untuk otomasi deteksi cacat di lini produksi industri (misal: pelapisan/coating dan pengelasan). Proyek ini merupakan inisiatif untuk GSPE.

Sistem ini menggunakan arsitektur *decoupled* yang dipisahkan menjadi 3 komponen utama, namun dikelola dalam satu *repository* (monorepo). Inspector memantau live feed dari kamera, trigger pengiriman batch ke server SAM3 untuk analisis, lalu me-review hasil segmentasi cacat dan generate laporan audit.

## Arsitektur & Workspace

| Component | Status | Description |
|---|---|---|
| `qc_frontend/` | **Active** | Vue 3 dashboard dengan 11 halaman, Carbon Design System, i18n bilingual, live `qc_server` API integration, Auto/Manual Live Monitor, annotated MJPEG detection feed/count/FPS, Auto presence-cycle crop results, shared Send-to-QC crop approval gate, Direct Inspection upload/server-camera/mobile-camera on-demand QC with preview stack and Send to QC Studio as a finished batch with persisted defects, Inspect Measurement task/view selector, drawn calibration, Image/Live/Mobile sources, line/circle/hole overlays, tolerance/evaluate, History, and Audit, pending raw QC images, image delete, QC Studio view/edit defect correction with icon-labeled floating edit tools, universal Cancel/Esc, SAM point/box assisted annotation, selected-defect vertex reshape, and linked row/polygon selection, re-run/reset controls, Settings object/QC/Quantity model sub-groups with native info tooltips, confidence split plus Quantity NMS tuning and target-class controls, Settings defect-class management/colors with free-type categories, production Media Detection Test/Process upload page with multi-image image mode, Quantity Detection Image/Video/Camera snapshot sources with active-class context chip, annotated canvas/filmstrip/crop evidence delete and crop-driven count correction, Reports per-run Defect Only or production Full Image PDF modes with QC Studio-colored overlays and per-image defect tables, and Quantity History combined crop inspect/delete, selected CSV/PDF export, and Send to QC |
| `qc_server/` | **Active (M0-M3 + streaming slices 1-3 + Auto/Manual redesign + Auto presence-cycle crop + Direct Inspection + Media Detection crop-to-QC + raw pending batches + manual defect CRUD + interactive SAM + re-run/reset + defect-class management + SAM3 prompt + Quantity Detection + Inspect Measurement)** | FastAPI + SQLite backend untuk async batch **defect** segmentation, raw image rows at submit, image row/file delete, nested manual defect CRUD, SAM point/box segmentation endpoint, batch re-run/reset, comprehensive idempotent defect-class seed/API, `mock` and real `sam3_prompt` defect strategies, CRUD metadata APIs, RTSP/USB camera streaming, annotated MJPEG detection/counting/FPS, one-shot capture, Auto presence-cycle best-frame lossless PNG crops with padding, per-camera/media crop sessions, crop approval endpoints, Direct Inspection detect/frame/to-QC endpoints with model-free auto-crop and persisted done-batch defects, sample image/video test endpoints, multi-image media crop-to-QC endpoints, Quantity detect-image plus full-res detect-camera snapshot with tunable NMS and switchable plain/open-vocab YOLOE target classes, temp crops with per-crop boxes/frame URL, checks save/list/detail/delete with persisted crop evidence, Quantity check-to-QC batch creation, OpenCV Inspect Measurement process API for image/Live Camera frames, manual calibration, candidate edge extraction, server-side tolerance evaluation, MeasurementRun persistence, History/delete, audit events, and real camera status monitor |
| `edge_app/` | Planned (after server) | Jetson Nano + TensorRT/`supervision` untuk **deteksi & penghitungan objek produk** + count-approval gate + live streaming |

### End-to-End Workflow

```
[Live Monitor] Start Camera raw preview
    → [Auto: Start/Stop Detection presence-cycle best-frame crop | Manual: Capture x N]
    → [Review & approve crop grid]
    → [Trigger: POST /api/batches dengan approved crop folder]
    OR [Direct Inspection] Stage upload(s) / server camera / mobile camera -> optional polygon mask -> Process QC preview stack -> Send to QC Studio done batch with defects
    OR [Media Detection] Stage upload(s) -> Run Test preview / Process uploaded media to crop review
    OR [Quantity Detection] Image upload / video frame / camera snapshot -> annotated canvas + filmstrip + crop evidence -> delete redundant crops if needed -> verify total verdict -> save check with persisted crop URLs -> optional Send to QC from Quantity History
    OR [Inspect Measurement] Image/Live/Mobile source -> draw calibration -> choose task/view -> OpenCV line/circle geometry -> tolerance/evaluate -> save History/Audit
    → [QC Studio: pending RAW image list/canvas + optional image delete]
    → [qc_server: async defect segmentation (mock or SAM3 prompt), polling]
    → [QC Studio: View-only review/export OR Edit mode floating tools + row/polygon selection + SAM point/box or manual add/delete/reshape/relabel + zoom/pan + mark reviewed + optional re-run/reset]
    → [Export: Crop/Full PNG + PDF Audit Report with annotated defect crops]
    → [Audit Log: auto-trails all actions]
```

Detail: [`docs/workflow.md`](./docs/workflow.md) | [`docs/PRD.md`](./docs/PRD.md)

> **Phase C-3 integration note:** The dashboard now uses the live `qc_server` API for QC Studio, Live Monitor's "Send to QC", Batch History, Reports, Audit Log, Cameras, Defect Classes, and Settings via the Vite dev proxy (`/api` → `http://localhost:8787`, same-origin, no CORS). Settings now persists model configuration, separate object-detection and QC confidence thresholds, `defect_strategy`, separate `active_model` / `qc_model` selections, and per-task inference devices (`auto`, `cpu`, or detected GPU index) to `/api/settings`, and manages enabled defect classes/colors through `/api/defect-classes`.
>
> **Live Streaming Slice 2.3:** Live Monitor consumes annotated MJPEG from `GET /api/cameras/{id}/detect-stream`; the browser renders it as an `<img>`, while the metric strip polls `GET /api/cameras/{id}/count` for `{ count, fps }`. The detection stream downscales before inference and caps loop FPS via `MQC_STREAM_MAX_WIDTH` / `MQC_STREAM_MAX_FPS` (defaults: `960` / `15`). `GET /api/cameras/{id}/stream` remains available as the raw MJPEG fallback. Drop YOLO `.pt` weights into `qc_server/models/`, then choose the active file in **Settings -> Model Configuration -> Object Detection Model**. Object detection uses server-only ML deps in `qc_server/requirements-ml.txt`.
>
> **Live Monitor Auto/Manual Flow:** Start Camera resets a per-camera crop session and shows raw MJPEG preview. Auto runs `GET /api/cameras/{id}/detect-stream` until Stop Detection and uses presence debounce to count/crop one best frame per object, suited to workers presenting parts one at a time without relying on ByteTrack. Manual calls `POST /api/cameras/{id}/capture` per click. Review & Send calls `POST /api/cameras/{id}/crop-session/finalize`, lets the operator check selected lossless padded PNG crop thumbnails, then calls `POST /api/cameras/{id}/crop-session/approve` and submits `POST /api/batches` with the approved crop folder.
>
> **Media Detection Crop-to-QC:** `/media-detection` is always visible in the sidebar. The page stages image/video uploads with drag-and-drop, shows the active model and confidence threshold, and waits for an explicit **Run detection** action before calling the server. Image mode supports multiple staged images; Test mode uploads each image to `POST /api/detect/image` for separate annotated base64 result cards and detection lists with confidence bars. Video Test uploads one video to `POST /api/detect/video` and plays `GET /api/detect/video/{id}/stream` as annotated MJPEG. Process image mode sends all staged images to `POST /api/detect/image/process` as multipart `files`, collecting immediate object crops into one crop-review dialog and one submitted QC batch; uploaded videos still use `POST /api/detect/video/{id}/extract` with polling via `GET /api/detect/video/{id}/extract/status`. Crop review uses `GET /api/detect/crop-session/{key}`, selected approval uses `POST /api/detect/crop-session/{key}/approve`, then the approved folder is submitted to QC. Uploaded videos are stored under `qc_server/data/uploads/`, which stays gitignored. Browser smoke is deferred to review.
>
> **Direct Inspection:** `/direct-inspection` is the first Quality Control submenu for on-demand QC. Operators can upload images, grab a full-resolution server-camera frame, or explicitly open the mobile browser camera over HTTPS with requested high-resolution constraints. Uploads stage until **Process QC**; each image may have one finished polygon processing mask, while unmasked images use the full frame. A mask takes priority over Auto-crop, runs inference in its bounded ROI, and returns defect coordinates remapped onto the original full image. Mobile mode can show a throttled, low-resolution live auto-crop guide using `POST /api/inspection/autocrop-preview`; final capture still uses full video resolution and `POST /api/inspection/detect`. The final response reports crop quality for operator review, overlays the applied mask on the result, and the optional debug toggle returns the original frame with the selected crop rectangle and FULL FRAME FALLBACK label. Approved captures send `{ key, defects, mask_polygon? }` through `POST /api/inspection/to-qc`; the polygon persists to the finished QC Studio batch and renders there as a non-editable Processing mask layer. Re-run and Reset still cover reprocessing or raw review.
>
> **Quantity Detection Snapshot Sources:** The dedicated Quantity group includes `/quantity` and `/quantity/history`. Quantity Detection uses the configured Quantity Detection model (`quantity_model`), optional target class list (`quantity_classes`), confidence threshold, Quantity NMS IoU (`quantity_nms_iou`), and class-agnostic merge toggle (`quantity_agnostic_nms`) for Image uploads, Video scrub-to-frame snapshots, and Camera snapshots. Empty target classes keep the existing plain YOLO/custom-trained path; non-empty target classes use an isolated YOLOE prompt-model cache and `set_classes()` so the shared object-detection cache is not mutated. Video mode draws the current `<video>` frame to a native-resolution canvas and posts it to the existing image endpoint; Camera mode shows the existing MJPEG preview but counts a full-resolution server-side `grab_one()` frame via `POST /api/quantity/detect/camera/{id}`. The backend returns one crop record per kept object with its source box and optional `frame_url`; the frontend uses that crop list as the single source of truth for canvas boxes, filmstrip badges, Evidence cards, session total/per-class tally, verdict, and save payload. Inspectors can delete redundant Evidence crops to correct over-detection before saving checks with active `source_type`, permanent per-image crop URLs, and a `QUANTITY_CHECK` audit log that includes the removed count. Quantity History lists saved checks, exports selected checks to CSV or PDF through one Export dialog, opens Inspect for a combined crop gallery, deletes checks plus their crop folders through `DELETE /api/quantity/checks/{id}`, and can send a check's persisted crop evidence to QC as a new pending batch through `POST /api/quantity/checks/{id}/to-qc` with a toast and Open in QC link. Browser smoke needs a real `.pt` selected as the Quantity model, a registered camera, and a scene that previously double-counted; YOLOE-26 open-vocab smoke is pending user GPU verification.
>
> **Defect Class Management:** Settings includes a compact **Defect Classes** section grouped by each distinct category in the data. Operators can enable/disable classes, add classes without hand-writing IDs, type a new category in the add/edit combobox, edit name/category/color, and delete obsolete classes. The backend seeds 25 canonical coating+welding variants idempotently, so existing databases gain missing classes without overwriting user edits. This is the configuration layer for SAM 3 prompt-based inference in Part B.
>
> **SAM 3 Prompt Strategy:** Batch QC can use `defect_strategy="sam3_prompt"` with a separate **QC / Segmentation Model** (`qc_model`) selected in Settings. The strategy lazily loads Ultralytics `SAM3SemanticPredictor`, embeds each crop once, queries each enabled defect-class name as a text prompt, filters by confidence, simplifies returned mask polygons in pure Python, and stores QC Studio-compatible defect polygons. `qc_device` selects `auto`, `cpu`, or a detected GPU index. GPU real-weight smoke remains a reviewer/local-server step.
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

When `qc_frontend/.certs/server-key.pem` and `server-cert.pem` exist, `scripts/dev.sh` enables HTTPS automatically. Open `https://<server-ip>:5757`; trust the mkcert `rootCA.pem` on each client device. Certificate files stay server-only and are gitignored.

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

### Pages (11 routes)

| Route | Page | Description |
|---|---|---|
| `/live` | **Live Monitor** | Camera selector (RaspyCam/RTSP/USB), Start Camera raw preview, Auto annotated MJPEG detection with presence-cycle best-frame crop, Manual capture, live object count/FPS, real online/offline status, Send to QC crop approval dialog |
| `/direct-inspection` | **Direct Inspection** | On-demand upload/server-camera/mobile-camera defect check with staged upload processing, per-image polygon ROI masks or full-frame fallback, full-image annotated results, and Send to QC Studio as a done batch with persisted defects and masks |
| `/measurement` | **Inspect Measurement** | One-side Image/Live Camera trigger/Mobile Camera capture with drawn reference-line calibration, task/view selection, OpenCV LSD/Hough lines and Hough circle candidates, hole geometry, per-item tolerance/evaluate, saved History, and Audit Log |
| `/qc` | **QC Studio** | 3-column inspection: pending raw image list/canvas, per-image delete, view-only default, persisted edit mode with icon-labeled floating Select/Draw/SAM point/SAM box/Reshape/Delete tools and universal Cancel/Esc, bidirectional row/polygon selection, cursor-aware draw/SAM/reshape/select/pan states, SAM-assisted or manual polygon add/delete/reshape/relabel, re-run/reset controls, batch sidebar (filter/search) + canvas (zoom/pan) + defect panel (keyboard nav, review workflow) |
| `/batches` | **Batch History** | Searchable table of all processed batches, filter by status, delete with confirmation |
| `/media-detection` | **Media Detection** | Always-visible production upload page with drag/drop staging, multiple-image image mode, explicit Run trigger, Test preview, and Process-to-QC crop export for images/videos |
| `/quantity` | **Quantity Detection** | Image/Video/Camera snapshot quantity count/verify workflow with active target-class context, selected annotated canvas, image filmstrip, crop-backed box overlays, per-image count badges, selected-image crop evidence delete, result band total/verdict from remaining crops, expected-total/tolerance target inputs, and Save toast |
| `/quantity/history` | **Quantity History** | Saved QuantityCheck records with search/filter, selected CSV/PDF export modal, combined crop Inspect dialog, Send to QC from Actions/Inspect with Open in QC link, and Delete confirmation |
| `/reports` | **Reports** | PDF audit report generator with summary, grouped annotated defect crops, approval fields |
| `/audit` | **Audit Log** | Auto-logged activity trail, filterable by action type |
| `/settings` | **Settings** | Camera CRUD, object/QC/Quantity model sub-groups with info tooltips, paired object/QC/Quantity confidence fields and inference-device selectors, Quantity NMS IoU + class-agnostic merge toggle, defect strategy, grouped defect-class enable/add/edit/delete/color with free-type categories, language/theme preferences |

### Key Features

- **Bilingual i18n** (Bahasa Indonesia / English) dengan toggle, persisted di localStorage
- **Light/Dark mode toggle** dengan Carbon Gray-100 dark theme, persisted di localStorage
- **Collapsible sidebar navigation** dengan 11 pages, reusable Vue SVG icon components, 280px expanded / 64px collapsed rail, native `title`/`aria-label` labels on collapsed icons, active parent-group tint, arrow-key navigation, and a refined `GSPE | MQC-AI` wordmark (centered `GSPE` when collapsed)
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
- **Direct Inspection**: Quality Control submenu for on-demand defect checks from uploaded images, server-camera frames, or mobile HTTPS camera captures. Uploads stage until Process QC; each image can use one polygon ROI mask (with inference coordinates remapped to the original full frame) or falls back to full-frame processing. Applied masks overlay the inspection result and persist to the non-editable QC Studio Processing mask layer through Send to QC Studio.
- **Inspect Measurement**: Image, registered Live Camera trigger, or HTTPS Mobile Camera capture enters one-side Measurement Studio. Every source is staged first; Live Camera uses `/api/measurements/capture`, Mobile Camera stages the client JPEG, then inspector draws a known reference line before clicking Process Measurement. Inspector selects task/view (`linear_dimension`, `inclination`, profile `bend_angle`, `hole_diameter`, `hole_center_distance`, `hole_edge_distance`, `hole_center_to_edge`), reviews OpenCV `LineSegmentDetector`/`HoughLinesP` or `HoughCircles` candidates, sets per-item nominal/tolerance (linear default `±2.0 mm`, angle default `±0.5°`), and Evaluate returns `PASS`, `FAIL`, or `REVIEW`. Results persist source image, calibration, geometry, task/view/method metadata, History, and audit events. Thickness remains a profile-metrology boundary; station matrix/homography, multi-view session, drawing recipe, and physical accuracy validation remain future work.
- **Measurement Studio layout**: QC Studio-style fixed-height desktop shell starts immediately below the application TopBar; no in-page heading, outer padding, or modal-like container. Fixed left/canvas/right positioning uses the same `280px / flex / 320px` rail model as QC Studio. The left Input/Calibration rail scrolls independently like the QC batch list, History has its own scroll region, and Measurement Items has its own right-panel scroll region. Source/process/status controls float over the canvas, which uses the same image-frame model as QC Studio for zoom/pan-safe SVG alignment; candidate edges use restrained 3px strokes with contrast halos, endpoints, and selected measurement labels. On narrow screens, the shell falls back to page scroll so stacked panels remain reachable.
- **Media Detection page**: always-visible upload workspace with drag/drop staging, multi-image image mode, active-model context, explicit Run trigger, invalid/no-model/error states, Test mode annotated result cards, and Process mode image/video lossless padded PNG object crops for shared review and QC batch submission
- **Model switchers**: `.pt` files in `qc_server/models/` are listed by `GET /api/models`; `GET /api/system/gpus` reports detected GPU indexes, names, VRAM, and utilization. Settings persists `active_model` for live object detection, `qc_model` for batch QC segmentation, and `quantity_model` for Quantity Detection, plus `object_detection_device`, `qc_device`, and `quantity_device` (`auto`, `cpu`, or detected GPU index), grouped into Object Detection / QC / Quantity blocks with native info tooltips and separate object/QC/Quantity confidence shown as decimal `0.00-1.00`; Quantity also has target classes for YOLOE open-vocab mode plus tunable NMS IoU and class-agnostic merge for overlapping detections
- **Quantity Detection**: dedicated count/verify workflow handles uploaded images, scrubbed video-frame snapshots, and full-resolution camera snapshots, overlays crop-backed boxes on the selected frame/image, provides filmstrip switching, shows selected-image object crop evidence, lets inspectors delete redundant crop cards to correct over-detection, derives session total/per-class counts and Pass/Fail from remaining crops, switches between plain custom-trained/prompt-free models and YOLOE open-vocab target classes via `quantity_classes`, tunes NMS IoU/class-agnostic merge to reduce duplicate boxes on one object, saves active `source_type` plus per-image `inputs` with permanent crop URLs, and provides Quantity History search/filter/selected CSV or PDF export/combined-crop Inspect/Delete plus Send to QC for saved crop evidence.
- **SAM 3 prompt QC strategy**: `sam3_prompt` uses enabled defect-class names as SAM 3 text prompts and writes confidence-filtered polygons for QC Studio
- **SAM click-to-segment**: QC Studio edit mode calls `POST /api/batches/{id}/images/{image_id}/segment` for point/box prompts, then saves the returned polygon through the existing defect add flow
- **Defect class management**: Settings groups defect classes by distinct category with on/total counts, enable toggles, free-type category add/edit, API-backed persistence, and auto-generated IDs for new classes
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

Implemented M0-M3 plus Live Streaming Slices 1-3, the Auto/Manual redesign, Auto presence-cycle crop, Direct Inspection, Media Detection crop-to-QC, Quantity Detection snapshot sources, batch deletion, raw pending batch rows, image row/file delete, nested manual defect CRUD, interactive SAM point/box segmentation, batch re-run/reset, defect-class management, real `sam3_prompt` QC strategy, dedicated QC confidence, and lossless padded PNG crop output: health/startup, SQLite schema, seeded cameras/defect classes/settings, comprehensive coating+welding idempotent defect-class seed data, optional auto-generated defect-class create IDs, metadata CRUD, audit log, async batch polling, `DELETE /api/batches/{id}` cleanup, `DELETE /api/batches/{id}/images/{image_id}` row + crop-file cleanup, `POST/PATCH/DELETE /api/batches/{id}/images/{image_id}/defects[/{defect_id}]` manual corrections, `POST /api/batches/{id}/images/{image_id}/segment` point/box SAM polygon generation, `POST /api/batches/{id}/reset`, deterministic `mock` defect strategy, Ultralytics SAM 3 text-prompt defect strategy, model-free Direct Inspection auto-crop, `POST /api/inspection/detect`, `GET /api/inspection/frame/{key}/frame.jpg`, `POST /api/inspection/to-qc` with persisted done-batch defects, `result.json` output, crop image serving, `GET /api/cameras/{id}/stream` raw MJPEG streaming, `GET /api/cameras/{id}/detect-stream` annotated MJPEG detection/counting stream with downscale/FPS cap and presence-cycle best-frame crop, `GET /api/cameras/{id}/count` returning count and FPS, one-shot `grab_one()` capture, per-camera/media crop sessions, `POST /api/cameras/{id}/crop-session/start`, `POST /api/cameras/{id}/capture`, `POST /api/cameras/{id}/crop-session/finalize`, `POST /api/cameras/{id}/crop-session/approve`, camera/media crop thumbnail serving with inferred content type, `/api/detect/*` sample image/video detection endpoints, multi-image image process crop export, async video crop extraction/status polling, media crop approval, shared quantity `run_quantity_snapshot()` for `POST /api/quantity/detect/image` and full-resolution `POST /api/quantity/detect/camera/{id}` with switchable `quantity_classes` plain/YOLOE open-vocab mode, tunable Quantity NMS, and temp object crop evidence carrying per-crop boxes plus optional `frame_url`, `GET /api/quantity/crops/{p1}/{p2}/{filename}`, `POST/GET/GET-by-id/DELETE /api/quantity/checks[/{id}]` with per-image `inputs` and permanent crop URLs, `POST /api/quantity/checks/{id}/to-qc` for copying saved Quantity crops into a pending QC batch, and background camera status monitoring. Real-weight SAM 3 GPU smoke and YOLOE-26 Quantity GPU smoke are pending.

Detection stream performance is configured with `MQC_STREAM_MAX_WIDTH` (default `960`) and `MQC_STREAM_MAX_FPS` (default `15`). Downscaling happens before detection so drawn boxes match the streamed frame.

Direct Inspection polygon masking is covered by a mocked Playwright browser flow: two staged uploads exercise one multipart `mask_polygon` request, one full-frame fallback request, result overlay rendering, and the mask-preserving QC handoff.

Crop sessions store source images under `qc_server/data/crops/<camera_id>/<session_ts>/` as `obj_NNN.png`. Start Camera resets the session; Auto detection appends one lossless PNG best-frame crop per debounced presence cycle and Manual Capture appends one-shot crops. Each crop uses about 5% bbox padding, clamped to the original frame, so fine defect texture stays lossless and edge defects keep context. Stop Detection leaves the buffer available for Review & Send; approved copies go under `approved/`.

Media Detection uploads require `python-multipart`. Test images return annotated JPEG data and serialized detections; the frontend can run this once per staged image. Test videos are saved to `qc_server/data/uploads/` and streamed back as annotated MJPEG using the active model. Process images post multipart `files` and crop detected objects from every valid image into one synchronous lossless padded PNG crop session; Process videos run a background presence-cycle extraction job and expose crop review/approval endpoints before QC batch submission.

Server-only detection dependencies are kept out of the laptop/base install. On the GPU server, install a CUDA-matched `torch` first, then `cd qc_server && .venv/bin/python -m pip install -r requirements-ml.txt`, copy `.pt` weights into `qc_server/models/`, choose **Object Detection Model**, **QC / Segmentation Model**, **Quantity Detection Model**, and each task's inference device in Settings, and run the backend. YOLOE open-vocab Quantity mode needs `yoloe-26l-seg.pt` in the models directory and target classes filled; do not commit the weight file.

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
- `2026-07-02-quantity-nms-tuning.md` - Quantity Detection NMS IoU and class-agnostic merge tuning for duplicate-count reduction
- `2026-07-03-quantity-evidence-delete.md` - Quantity Evidence crop delete and crop-driven count correction
- `2026-07-03-quantity-snapshot-sources.md` - Quantity Detection Video and Camera snapshot sources
- `2026-07-03-direct-inspection.md` - Direct Inspection upload/server-camera/mobile-camera on-demand QC flow

---
*Dokumen ini harus selalu diperbarui setiap kali ada penambahan fitur utama atau perubahan arsitektur. Lihat protocol di `AGENTS.md` > Documentation Maintenance.*
