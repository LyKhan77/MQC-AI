# CHANGELOG

> **Agent Memory Contract.** This file is the single source of truth for what changed, when, and why. Every AI agent working on this repo MUST read this file before starting work and MUST append an entry after committing changes. See `AGENTS.md` section "Documentation Maintenance" for the full contract.

All notable changes to the MQC-AI project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [Semantic Versioning](https://semver.org/).

Each entry contains:
1. Standard Keep a Changelog categories (Added / Changed / Fixed / Removed)
2. **Current Codebase State** table tracing what was developed and the resulting state

---

## [Unreleased] - 2026-06-27 - Phase C-3: Cameras + Settings on Live API

### Summary

Finished the remaining frontend/backend integration gap for Cameras and Settings. Camera CRUD now uses `GET/POST/PATCH/DELETE /api/cameras`, Settings persists model config through `GET/PUT /api/settings`, and the UI can select `defect_strategy` so new batches record the chosen backend strategy in `model_info.strategy`.

### Added

- `qc_frontend/src/api/client.js` - `apiPut()` and `apiDelete()` helpers.
- `qc_frontend/src/api/cameras.js` - live camera CRUD API wrapper.
- `qc_frontend/src/api/settings.js` - settings API wrapper with snake_case/camelCase mapping and numeric confidence coercion.
- Unit tests for client PUT/DELETE, camera create/delete, and settings mapping/update. Frontend suite: 23 tests green.
- i18n keys `settings.defectStrategy`, `settings.strategyMock`, and `settings.strategySam3` in `id.js` and `en.js`.

### Changed

- `useCameras.js` now sources cameras from the live API, exposes `refresh()`, and refreshes after add/edit/delete.
- `useSettings.js` now sources model settings from the live API and includes `defectStrategy`.
- `Settings.vue` refreshes cameras/settings on mount, awaits async camera CRUD, saves settings through the API, and adds a defect-strategy selector.
- `LiveMonitor.vue` refreshes cameras on mount so its selector reflects backend camera state.
- `README.md` and `AGENTS.md` now describe the dashboard as live API-backed.

### Fixed

- `Settings.vue` `saveSettings()` now reads `settings.value.*` in script setup instead of the ref object itself, so detection model, segmentation model, confidence threshold, and defect strategy persist correctly.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Camera data | 2026-06-27 | `src/api/cameras.js` + API-backed `useCameras` | Settings camera CRUD and Live Monitor camera selector read/write `qc_server`. |
| Settings data | 2026-06-27 | `src/api/settings.js` + API-backed `useSettings` | Model config persists through `/api/settings`; `defectStrategy` is user-selectable. |
| Frontend API client | 2026-06-27 | `apiPut` and `apiDelete` helpers | `src/api/*` supports all methods needed by dashboard CRUD. |
| Settings UI | 2026-06-27 | Async handlers + defect-strategy selector | Settings drives backend behavior for future real inference strategy. |
| Dashboard integration | 2026-06-27 | Cameras + Settings migrated off localStorage mock | Dashboard data is API-backed; Live Monitor detection simulation remains mock until edge app exists. |

### Notes

- Branch: `feat/phase-c3-cameras-settings` (unmerged; pushed for plan-author review).
- Deviations: none in implementation scope. `AGENTS.md` was also updated to satisfy the repo documentation-maintenance contract.

---

## [Unreleased] - 2026-06-27 — Phase C-2.1: Batch Review Sign-off + Review-Progress Column

### Summary

Closed the QC workflow gap where a batch was stuck at `done`. QC Studio now has an explicit **"Mark Reviewed" sign-off** button (enabled only once every image is reviewed) that PATCHes the batch `done → reviewed` (with reviewer `inspector@gspemail.com`) and logs `BATCH_REVIEWED`. The backend `BatchSummary` now carries a computed `reviewed_count` (number of that batch's images with `reviewed == true`, computed in the list query — no schema/migration change). Batch History gained a **"Reviewed" column** showing `X/Y` progress and visually distinct pills: `done` is now neutral (surface-1 + hairline) so the green `reviewed` pill stands out as "QC complete". The frontend `src/api/batches.js` layer gained `patchBatch()` and the `reviewedCount` mapping.

### Added

- `qc_server/app/schemas.py` — `BatchSummary.reviewed_count: int = 0`.
- `qc_server/app/routers/batches.py` — `list_batches` now computes reviewed counts via a `func.count(Image.id)` grouped by `batch_id` filter (`reviewed.is_(True)`).
- `qc_frontend/src/api/batches.js` — `patchBatch(batchId, { status, reviewer })`; `mapBatchSummary` now returns `reviewedCount`.
- `qc_frontend/src/composables/useInspection.js` — `markReviewed()` action (PATCHes current batch to `reviewed` with `REVIEWER = 'inspector@gspemail.com'`).
- `qc_frontend/src/components/BatchSidebar.vue` — "Mark Reviewed" sign-off button with `signedOff` ref (reset on new batch load); `handleSignOff` logs `BATCH_REVIEWED`.
- `qc_frontend/src/views/BatchHistory.vue` — "Reviewed" column (`X/Y`) and `columnReviewed` header.
- i18n keys: `qc.markReviewed`, `qc.reviewed` (id + en); `batches.columnReviewed` (id + en).
- Backend test `test_list_batches_includes_reviewed_count`; frontend test `patchBatch sends status + reviewer` and updated `listBatches` mapping assertion. Suites: backend 24 green, frontend 17 green.

### Changed

- `BatchHistory.vue` `.status-pill.status-done` is now neutral (`surface-1` bg, `hairline` border) instead of green, so the green `reviewed` pill reads as "QC complete".
- `README.md`: notes that QC Studio has a "Mark Reviewed" sign-off and that Batch History shows review progress (X/Y) and distinct status pills.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Batch status workflow | 2026-06-27 | Explicit sign-off transitions `done → reviewed` via `PATCH /api/batches/{id}` | Batch reaches terminal `reviewed` state; no longer stuck at `done`. |
| Backend `BatchSummary` | 2026-06-27 | Computed `reviewed_count` on the list endpoint | `GET /api/batches` items include `reviewed_count: int`. |
| `src/api/batches.js` | 2026-06-27 | `patchBatch` + `reviewedCount` mapping | Frontend can sign off batches; mapper carries reviewed count. |
| QC Studio | 2026-06-27 | "Mark Reviewed" button in `BatchSidebar` (guarded by all-reviewed) | Explicit completion gate; logs audit entry. |
| Batch History | 2026-06-27 | "Reviewed" column + neutral `done` pill | Progress visible at a glance; `reviewed` distinct from `done`. |

### Notes

- Branch: `feat/fe-be-integration` (unmerged; left for plan-author review).
- Deviations: none. Reviewer identity is the single-user MVP constant `inspector@gspemail.com`. Backend `reviewed_count` is computed, not stored.
- Open: server end-to-end smoke (Task 4 Step 5) to be run on the Linux server.

---

## [Unreleased] - 2026-06-27 — Phase C-2: Batch History + Reports on Live API

### Summary

Fixed the two regressions left by Phase C. Batch History and Reports now source their batch lists from `GET /api/batches` (via a new `listBatches()` + `mapBatchSummary` snake_case→camelCase mapper in `src/api/batches.js`). `useBatchHistory` dropped localStorage/mock and now exposes a `refresh()` that pulls from the API. `BatchHistory.vue` "Open" passes the real `batch.id` to QC Studio (`/qc?batch=<id>`), and the status filter + pills cover backend statuses (`done`/`failed` added alongside `reviewed`/`processing`). `Reports.vue` selects a batch and loads the real result via `loadBatch(id)`, removing the `/mock/batch-shift1.json` 404 source. Also hardened `pollBatchUntilDone` with a `maxAttempts` timeout (default 600) that throws `Batch polling timed out`. Cameras and Settings remain on localStorage mock (Phase C-3, see Appendix A of the C-2 plan).

### Added

- `qc_frontend/src/api/batches.js` — `mapBatchSummary(s)` (snake_case → camelCase) and `listBatches()` (`GET /batches`).
- `pollBatchUntilDone` gained `{ maxAttempts = 600 }`; throws `Error('Batch polling timed out')` after `maxAttempts` non-terminal polls (open review finding from Phase C).
- i18n keys `batches.filterDone` / `batches.filterFailed` (id + en).
- Unit tests for `listBatches` (mapping) and the poll timeout (2 new). Full frontend suite: 16 tests green (5 in `batches.test.js`).

### Changed

- `useBatchHistory.js`: localStorage/mock removed; now `batches` starts empty and `refresh()` populates from `listBatches()`. Removed unused `addBatch`/`updateBatch`/`getById`/`pendingCount` (verified no `.vue` consumer).
- `BatchHistory.vue`: calls `refresh()` on mount; `openBatch` navigates to `/qc?batch=<id>`; status filter options now `reviewed`/`done`/`processing`/`failed` (dropped mock-only `pending`); added `.status-pill.status-done` / `.status-failed` CSS.
- `Reports.vue`: calls `refresh()` on mount; `selectBatch(id)` calls `loadBatch(id)` (removed the hard-coded `loadBatch('/mock/batch-shift1.json')` 404 source).
- `README.md`: Phase C integration note updated to say Batch History + Reports are now live-API too; only Cameras and Settings remain on mock pending Phase C-3.

### Fixed

- `Reports.vue` no longer triggers `GET /api/batches//mock/batch-shift1.json/status → 404` (regression from Phase C).
- `BatchHistory.vue` "Open" no longer navigates to an empty QC Studio (now passes the real `batch.id`).

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Batch History page | 2026-06-27 | Sourced from `GET /api/batches`; opens QC Studio by real id | Live-API; status filter covers backend vocab. |
| Reports page | 2026-06-27 | Sourced from `GET /api/batches`; loads real result by id | Live-API; mock-path 404 eliminated. |
| `pollBatchUntilDone` | 2026-06-27 | `maxAttempts` timeout guard | Bounded polling; throws on timeout. |
| `useBatchHistory` | 2026-06-27 | Dropped localStorage/mock; exposes `refresh()` | Thin API consumer. |
| Cameras / Settings | 2026-06-27 | Untouched | Still localStorage mock; deferred to Phase C-3. |

### Notes

- Branch: `feat/fe-be-integration` (unmerged; left for plan-author review).
- Deviations: none. API boundary mapping matches `qc_server/app/schemas.py` `BatchSummary`.
- Open questions: server end-to-end smoke (Task 4 Step 3) to be run on the Linux server.

---

## [Unreleased] - 2026-06-26 — Phase C Core Slice: Frontend ↔ Backend Integration

### Summary

Wired the Vue frontend's core QC vertical slice to the live `qc_server` API. Live Monitor "Send to QC" now POSTs a real batch, QC Studio polls for status then loads the live result, image review fires a best-effort PATCH, and the Audit Log reads/writes through the API. A new pure `src/api/` layer (unit-tested with mocked `fetch`) isolates all HTTP and snake_case mapping from Vue components. Cameras, Settings, and Batch History remain on localStorage mock (deferred to Phase C-2).

### Added

- `qc_frontend/src/api/client.js` — `apiGet`/`apiPost`/`apiPatch` helpers; base `import.meta.env.VITE_API_BASE ?? '/api'`; throw `HTTP <status> ...` on non-2xx.
- `qc_frontend/src/api/batches.js` — `submitBatch`, `getBatchStatus`, `getBatchResult`, `patchImageReviewed`, `pollBatchUntilDone` (resolves on `done`/`reviewed`, throws on `failed`).
- `qc_frontend/src/api/audit.js` — `postAudit`, `listAudit`.
- Unit tests for `src/api/client.test.js` (3), `src/api/batches.test.js` (3), `src/api/audit.test.js` (2). Full frontend suite: 14 tests green. No jsdom / @vue/test-utils added.
- Vite dev proxy: `/api` → `http://localhost:8787` (no CORS, same-origin calls only).
- i18n keys `sendToQC.sourcePath`, `sourcePathPlaceholder`, `sendFailed` (id + en).

### Changed

- `useInspection.js`: `loadBatch(batchId)` now polls the live API then fetches the result; exposes `currentBatchId` and `progress` refs; `toggleReviewed` also best-effort PATCHes the image review state (keeps localStorage for offline resilience).
- `BatchSidebar.vue`: auto-loads the batch from `route.query.batch` on mount and on route change; shows polling progress while loading.
- `LiveMonitor.vue`: "Send to QC" now calls `submitBatch` and navigates to `/qc?batch=<batch_id>`; dialog gained a server-side Source Folder (crops path) field; removed `useBatchHistory` from this path.
- `useAuditLog.js`: `log()` also POSTs to `/api/audit` (best-effort); new `refresh()` replaces logs from `GET /api/audit`.
- `AuditLog.vue`: calls `refresh()` on mount.
- `README.md`: notes that QC Studio + Live Monitor "Send to QC" now use the live API via the Vite `/api` proxy, and that `source_path` is a folder on the `qc_server` host.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Frontend QC batch flow | 2026-06-26 | Live Monitor submit → poll → QC Studio live load → review PATCH → audit API | Live-API for the core slice; verified by `npm run build` + 14 unit tests. Server end-to-end smoke pending on Linux server. |
| `qc_frontend/src/api/` | 2026-06-26 | Pure HTTP + polling layer with snake_case mapping | Unit-tested (8 new tests); no Vue/DOM dependencies. |
| Cameras / Settings / Batch History | 2026-06-26 | Untouched | Still localStorage mock; migration deferred to Phase C-2 (Appendix A of the integration plan). |
| `qc_server/` | 2026-06-26 | Unchanged (M0-M3) | Backend contract matched; no server changes required for this slice. |

### Notes

- Branch: `feat/fe-be-integration` (unmerged; left for plan-author review).
- Deviations: none. All API shapes match `qc_server/app/schemas.py` (`BatchCreate`, `BatchStatusOut`, `BatchResult`, `ImagePatch`, `AuditLogIn`).
- Open questions: server-side smoke (Task 6 Step 4) to be run by the user on the Linux server.

---

## [Unreleased] - 2026-06-26 — Backend Planning (`qc_server`)

### Summary

Planning-only milestone (no code yet). Locked backend architecture for `qc_server` and clarified the end-to-end flow. Edge app re-scoped to **product** object detection + counting + a count-approval gate; QC re-scoped to **defect** segmentation with a pluggable, Settings-selectable strategy.

### Added

- `docs/superpowers/plans/qc-server-plan.md` (gitignored) — locked decisions, folder structure, SQLite schema, API endpoints, pluggable defect-strategy interface, polling job flow, milestones M0→M4, and edge-app flow reference.

### Changed

- **Architecture decisions locked**: build `qc_server` first; async via **polling**; **SQLite + filesystem** persistence; **single-user** (auth deferred); Edge→QC trigger via **folder drop + `POST /api/batches`**; per-camera counting mode (`tracking` via `supervision` ByteTrack+LineZone, or `single` for 1-frame-1-object metal sheet); QC defect inference **pluggable** (`mock` → `sam3_prompt` → future `detector_refine`/`anomaly`).
- `docs/PRD.md` → v1.2.0: corrected component responsibilities + pluggable defect strategy + tech/NFR updates.
- `docs/workflow.md`: updated architecture diagram and operational phases (added count inspection gate + trigger; renumbered to 5 phases).
- `AGENTS.md`: updated Backend/Edge planned features + Current State (Backend planning approved).
- `README.md`: updated workspace table, end-to-end workflow, and implementation-plans list.

### Current Codebase State

| Area | State |
|---|---|
| `qc_frontend/` | Unchanged — functional with mock data. |
| `qc_server/` | **Planned, approved.** No code yet; plan at `docs/superpowers/plans/qc-server-plan.md`. Next: milestone M0 scaffold. |
| `edge_app/` | Planned (after `qc_server`). Flow documented. |
| Docs | PRD/workflow/AGENTS/README synced to corrected flow. |

---

## [0.3.0] - 2026-06-26

### Summary

Implemented `qc_server` milestones M0-M3 with FastAPI, SQLite, CRUD endpoints, async batch polling, deterministic `mock` defect strategy, result JSON writing, and crop image serving. Real SAM3 remains deferred to the later M4 plan.

### Added

- `qc_server/` backend application with FastAPI app/config, SQLAlchemy 2.0 SQLite models, Pydantic schemas, startup table creation, and seeded cameras/defect classes/settings.
- CRUD APIs for `/api/cameras`, `/api/defect-classes`, `/api/settings`, and `/api/audit`.
- Async batch API: `POST /api/batches`, status polling, result fetch, history list, batch patch, and per-image review patch.
- Pluggable inference interface under `app/services/inference/` with deterministic `MockStrategy`; filenames containing `clean` return no defects.
- Storage helpers, in-memory job progress map, batch pipeline, `result.json` output, and `/api/images/{image_id}/file` crop serving.
- Backend test suite covering health/startup/models/seeding/CRUD/mock strategy/pipeline/batches/images.
- `qc_server/README.md` with setup, run, test, configuration, and strategy notes.

### Changed

- `AGENTS.md`: backend tech stack, project structure, commands, key features, and current state now reflect `qc_server` M0-M3 completion.
- `README.md`: workspace table now marks `qc_server/` active and includes backend commands.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| `qc_server/` | 2026-06-26 | FastAPI + SQLite backend through M0-M3 | Active: mock strategy, polling batch pipeline, CRUD APIs, image serving, 23 backend tests passing |
| Defect Inference | 2026-06-26 | `DefectStrategy` protocol + deterministic `MockStrategy` | `sam3_prompt` intentionally deferred to M4; API/DB ready for strategy switch |
| Docs | 2026-06-26 | Backend README + root docs sync | README/AGENTS/CHANGELOG reflect backend implementation state |

---

## [0.2.0] - 2026-06-26

### Summary

Full frontend overhaul: Carbon Design System migration (light/dark), sidebar navigation shell, 6 routed pages, i18n bilingual, rich mock data layer, and P0 bug fixes.

### Added

- **Carbon Design System** with light mode (default) and dark mode (Carbon Gray-100 theme).
  - CSS variables for both themes in `style.css`, toggled via `data-theme` attribute on `<html>`.
  - IBM Plex Sans (300/400/600) + IBM Plex Mono fonts via `@fontsource`.
  - Flat geometry (0px border-radius), 1px hairline borders, surface hierarchy.

- **Theme toggle** composable (`useTheme.js`).
  - Default follows `prefers-color-scheme`, user can override via toggle button in top bar.
  - Persisted in `localStorage` key `mqc-theme`.

- **Collapsible sidebar navigation** (`AppSidebar.vue`) + slim top bar (`TopBar.vue`).
  - 6 nav items with SVG icons: Live Monitor, QC Studio, Batch History, Reports, Audit Log, Settings.
  - Sidebar collapse/expand button; collapsed state shows icons only (56px width).

- **i18n bilingual system** (Indonesian / English).
  - Composable `useI18n.js`, locale files `src/assets/locales/id.js` and `en.js`.
  - Language toggle in top bar (ID/EN button) and in Settings page.
  - Persisted in `localStorage` key `mqc-lang`.

- **Live Monitor page** (redesigned).
  - Camera selector dropdown (reads from `useCameras` composable).
  - Start/Stop Detection buttons with connecting state.
  - Mock object counter, FPS, temperature indicators with live-updating values.
  - Mock bounding box overlay on video feed placeholder.
  - Send to QC dialog: batch name input with auto-timestamp, source camera, image count, model info.

- **QC Studio page** (redesigned).
  - Batch sidebar: search input, filter chips (All/Defect/Clean/Unreviewed), sort dropdown (name/defect count), skeleton loading state, review progress bar, error display.
  - Inspection canvas: zoom (mouse wheel, 50%-500%), pan (drag), annotation toggle, reset zoom button.
  - Defect panel: keyboard navigation (Arrow keys to navigate images, Spacebar to toggle reviewed).
  - Review workflow: mark/unmark reviewed per image, visual checkmark in batch list, reviewed set persisted in `localStorage`.

- **Batch History page** (new).
  - Table of all processed batches from `useBatchHistory` composable.
  - Search by batch name, filter by status (reviewed/pending/processing).
  - Click row to open batch in QC Studio. Generate Report shortcut.

- **Reports page** (new).
  - Batch selector dropdown.
  - Summary cards: total images, clean, defective, defect rate.
  - Defect detail breakdown per image with color-coded tags.
  - PDF generation via `jspdf`: audit report with batch info, summary, defect table, signature/approval fields.

- **Audit Log page** (new).
  - Table of all activity from `useAuditLog` composable.
  - Search by detail/user, filter by action type.
  - Auto-logs from all user actions (camera start/stop, batch sent/loaded, image reviewed, export, report generated, settings changed, camera CRUD).

- **Settings page** (new).
  - Camera management: table with add/edit/delete (CRUD), camera form (name, type, source, location).
  - Model configuration: detection model, segmentation model, confidence threshold slider.
  - Preferences: language toggle (ID/EN), theme info.

- **Mock data layer** (`utils/mockData.js`).
  - 3 cameras (RaspyCam CSI, RTSP, USB), 5 batch history entries, 15 audit log entries, default settings.
  - All persistent in `localStorage` with seed-on-first-load pattern.

- **5 new composables**: `useI18n.js`, `useCameras.js`, `useBatchHistory.js`, `useAuditLog.js`, `useSettings.js`.

- **`docs/superpowers/plans/frontend-overhaul-plan.md`**: full implementation plan for this overhaul.

### Changed

- **`DESIGN.md`**: replaced GSPE Corporate Dark Theme with Carbon Design System spec. Added light + dark mode token tables, type scale, spacing system, component specs, and implementation rules.

- **`index.html`**: updated `<html lang="id" data-theme="light">`, title to `GSPE MQC-AI Dashboard`.

- **Router** (`router/index.js`): expanded from 2 routes to 6 routes with named routes.

- **`App.vue`**: replaced top-nav horizontal with sidebar + topbar shell layout.

- **`style.css`**: added Carbon CSS variables (light + dark blocks), legacy alias mapping, page-container/page-header shared styles. Removed old top-nav styles.

- **`useInspection.js`**: added `loading`, `error`, `reviewed`, `reviewedCount`, `toggleReviewed`, `isReviewed`. Added simulated network delay (1.2s) and try/catch error handling. Reviewed state persisted in `localStorage`.

### Fixed

- **`export.js` hardcoded defect colors** (P0): `resolveColor()` now reads CSS variables dynamically via `getComputedStyle(document.documentElement).getPropertyValue('--defect-{type}')` instead of hardcoded hex values from the old theme. Fallback chain: CSS var > `--color-ink-subtle` > `#8c8c8c`.

- **Load Batch zero feedback** (P0): added skeleton loading state, simulated network delay, visible error message in sidebar, disabled button during loading.

- **Export silent fail** (P0): added try/catch around `loadImageEl()` in `exportCrop` and `exportFull` with console error logging.

### Removed

- `@fontsource/inter` and `@fontsource/jetbrains-mono` imports from `style.css` (replaced by IBM Plex fonts). Packages remain installed but unused.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Design System | 2026-06-26 | Carbon Design System with light/dark mode tokens | `style.css` has `:root[data-theme='light']` and `:root[data-theme='dark']` blocks; all components use `--color-*` tokens |
| Navigation Shell | 2026-06-26 | Collapsible sidebar + slim top bar | `App.vue` renders `AppSidebar.vue` (220px/56px) + `TopBar.vue` (48px) + `<router-view>` |
| Routing | 2026-06-26 | 6 named routes | `/live`, `/qc`, `/batches`, `/reports`, `/audit`, `/settings`; `/` redirects to `/live` |
| i18n | 2026-06-26 | Bilingual ID/EN with `useI18n` composable | ~300 translation strings in `locales/id.js` and `locales/en.js`; toggle in top bar + Settings |
| Live Monitor | 2026-06-26 | Camera selector + detection trigger + send-to-QC dialog | `LiveMonitor.vue` reads `useCameras`, mock detection loop, `SendToQCDialog` inline modal |
| QC Studio | 2026-06-26 | Review workflow + zoom/pan + filter/search + keyboard nav | `BatchSidebar` has filter chips + skeleton; `InspectionCanvas` has zoom/pan toolbar; `DefectPanel` has arrow/space keyboard handlers |
| Batch History | 2026-06-26 | Table view of all batches | `BatchHistory.vue` reads `useBatchHistory`, search + status filter, row click navigates to QC |
| Reports | 2026-06-26 | PDF audit report generator | `Reports.vue` uses dynamic `import('jspdf')`, generates `{batch_name}_report.pdf` |
| Audit Log | 2026-06-26 | Activity trail table | `AuditLog.vue` reads `useAuditLog`, search + action filter, auto-logged from all composables |
| Settings | 2026-06-26 | Camera CRUD + model config + preferences | `Settings.vue` manages `useCameras`, `useSettings`, `useI18n`; all changes logged via `useAuditLog` |
| Mock Data | 2026-06-26 | Rich mock layer with localStorage persistence | `mockData.js` seeds 3 cameras, 5 batches, 15 logs on first load; composables auto-seed if `localStorage` empty |
| Export Utils | 2026-06-26 | Dynamic CSS variable color resolution | `export.js` `resolveColor()` reads `getComputedStyle` instead of hardcoded hex |

---

## [0.1.0] - 2026-06-25

### Summary

Initial frontend scaffold: Vue 3 + Vite project, 2-page dashboard (Live Monitor + QC Studio), GSPE Corporate Dark Theme, mock batch data.

### Added

- Vue 3 + Vite project with Vue Router.
- `LiveMonitor.vue`: live video feed placeholder with status pill (ONLINE/OFFLINE), FPS/temperature metrics, MJPEG stream URL display.
- `QCStudio.vue`: 3-column layout (BatchSidebar / InspectionCanvas / DefectPanel).
- `BatchSidebar.vue`: Load Batch button, batch list with filename + defect count + status dot.
- `InspectionCanvas.vue`: image display with SVG polygon overlay for defect annotations, hover cross-panel interaction.
- `DefectPanel.vue`: coating/welding defect list with confidence percentage, export crop/full buttons.
- `useInspection.js`: shared singleton state (batch, selectedId, hoveredDefectId, loadBatch, selectImage).
- `utils/defect.js`: defect type to CSS variable color mapping + polygon bounding box utility.
- `utils/export.js`: canvas rendering with polygon overlay, crop/full export with download.
- Mock data: `public/mock/batch-shift1.json` with 3 images (2 defective, 1 clean).
- `DESIGN.md`: GSPE Corporate Dark Theme spec (navy blue palette, gold accent, defect color tokens).
- `docs/PRD.md`: Product Requirements Document.
- `docs/workflow.md`: System workflow and architecture diagram.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Project Scaffold | 2026-06-25 | Vue 3 + Vite + Vue Router | `package.json` with vue@3.5, vite@8, vue-router@4 |
| Frontend Shell | 2026-06-25 | 2-page horizontal nav | `App.vue` with top-nav, `/live` and `/qc` routes |
| QC Studio | 2026-06-25 | 3-column inspection layout | BatchSidebar (280px) + Canvas (flex) + DefectPanel (320px) |
| Mock Data | 2026-06-25 | Single batch JSON | `public/mock/batch-shift1.json` with 3 images, polygon coordinates |
| Design System | 2026-06-25 | GSPE Dark Theme tokens | `style.css` with navy palette (`#031124`, `#06244A`), gold accent, defect colors |

---

## How to Update This File

**Every AI agent MUST follow this protocol when committing changes:**

1. **Read this file first.** Understand what was done before. Do not duplicate entries.
2. **After committing code changes**, append a new entry under `[Unreleased]` (or create a new version section if the user requests a release).
3. **Entry granularity**: one entry per feature, file logic, or significant change. Not per commit, not per session.
4. **Each entry must include**:
   - **Summary**: 1-2 sentence plain-language description.
   - **Added / Changed / Fixed / Removed**: bullet points with specific file names and what changed.
   - **Current Codebase State** table: one row per area affected, with columns `Area / Feature | Timeline | What Was Developed | After the Change`.
5. **Link the entry** in `AGENTS.md` > `Current State` > `Detailed Log` pointer.
6. **Be specific**: file names, composable names, CSS variable names, route names. Vague entries like "improved UI" are useless to the next agent.
7. **Do not delete historical entries.** Append only. Mistakes are corrected in new entries, not by rewriting old ones.
