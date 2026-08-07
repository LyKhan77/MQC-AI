# Inspect Measurement Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a one-image, one-side, semi-automatic measurement workflow: upload → calibrate → process → review edge candidates → set per-item tolerance → evaluate → save/history/audit.

**Architecture:** Keep measurement logic server-side in a small OpenCV service. Use the existing Vue API client, Carbon layout, SQLite/SQLAlchemy, file storage, and audit router. Store one prototype run with measurement items in a JSON column; avoid a separate measurement-item table until real recipe/versioning requires relational queries.

**Tech Stack:** Vue 3, Vue Router, vanilla CSS, FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite, OpenCV headless, NumPy, Vitest, Vue Test Utils, pytest, FastAPI TestClient.

## Global Constraints

- Prototype input is image upload only.
- One image represents one inspected side.
- No CAD/PDF parser, camera capture, multi-view session, 3D inference, trained model, or new dependency.
- Calibration is required before a trustworthy mm result.
- OpenCV returns candidates; inspector confirms/corrects geometry.
- Default tolerance is `±2.0 mm` for linear items and `±0.5°` for angle items.
- `PASS` requires valid calibration, valid geometry, complete nominal/tolerance, and measured value inside limits.
- Invalid/ambiguous/low-confidence measurement returns `REVIEW`.
- Reuse existing `api/client.js`, `useAuditLog.js`, i18n, settings/theme tokens, and startup migration style.
- All user-facing strings go into both locale files.
- Use `apply_patch` for edits. Do not alter the existing standalone HTML demo.

---

### Task 1: Define measurement math and service contract

**Files:**
- Create: `qc_server/app/services/measurement.py`
- Create: `qc_server/tests/test_measurement_service.py`
- Modify: `qc_server/app/schemas.py`

**Interfaces:**
- `calibrate_reference(point_a, point_b, known_mm) -> CalibrationResult`
- `measure_geometry(item_type, points, calibration) -> MeasurementResult`
- `evaluate_item(measured, nominal, tolerance, confidence, calibration_valid) -> status/result`
- Pydantic payloads for calibration, geometry, candidate, measurement item, process output, and saved run.

- [ ] Write failing tests for px-to-mm conversion, zero/negative calibration rejection, nominal ± tolerance bounds, angle evaluation, and `REVIEW` gates.
- [ ] Write failing tests for a synthetic horizontal/vertical line producing deterministic measurement output.
- [ ] Implement pure math and validation without database or HTTP dependencies.
- [ ] Implement candidate serialization with endpoint coordinates, pixel length, angle, confidence, and source method.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurement_service.py -v` from `qc_server/`.

### Task 2: Implement OpenCV candidate extraction

**Files:**
- Modify: `qc_server/app/services/measurement.py`
- Create: `qc_server/tests/test_measurement_cv.py`

**Interfaces:**
- `process_image(frame, calibration, options) -> ProcessMeasurementResult`

- [ ] Add failing synthetic-image tests for a clear rectangle and a low-signal image.
- [ ] Implement grayscale/denoise/edge preprocessing with existing OpenCV and NumPy only.
- [ ] Use `LineSegmentDetector` first; keep `HoughLinesP` as a fallback when candidate count is insufficient.
- [ ] Normalize endpoint ordering, remove short/noisy segments, deduplicate near-collinear candidates, and calculate confidence.
- [ ] Return `REVIEW` readiness when no usable candidate or calibration is invalid; never fabricate a PASS measurement.
- [ ] Run focused CV tests and inspect candidate coordinates against synthetic fixtures.

### Task 3: Add measurement persistence and API

**Files:**
- Modify: `qc_server/app/models.py`
- Modify: `qc_server/app/schemas.py`
- Create: `qc_server/app/routers/measurements.py`
- Modify: `qc_server/app/main.py`
- Create: `qc_server/tests/test_measurements.py`

**Interfaces:**
- `POST /api/measurements/process` — multipart image + calibration/options; returns image metadata, candidates, calibration, and readiness.
- `POST /api/measurements` — saves a named evaluated run.
- `GET /api/measurements` — lists saved runs newest first with summary fields.
- `GET /api/measurements/{run_id}` — returns complete run detail.
- `DELETE /api/measurements/{run_id}` — deletes run metadata and owned source file.
- `GET /api/measurements/files/{run_id}/{filename}` — serves contained source image.

- [ ] Add failing API tests for invalid image, process response, missing calibration, save, list, detail, delete, file serving, and path containment.
- [ ] Add `MeasurementRun` with manual name, timestamps, source metadata, calibration JSON, items JSON, summary verdict, and processing metadata.
- [ ] Add startup directory creation and lightweight `ensure_column` migration if needed by existing SQLite databases.
- [ ] Store uploaded source image under a measurement-owned directory; sanitize filenames and reject traversal.
- [ ] Wire process endpoint to the measurement service without loading any trained model.
- [ ] Save endpoint recomputes item limits/status server-side before persistence.
- [ ] Write `MEASUREMENT_PROCESSED`, `MEASUREMENT_EVALUATED`, `MEASUREMENT_SAVED`, and `MEASUREMENT_DELETED` audit records at the corresponding server actions.
- [ ] Include router in `qc_server/app/main.py`.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurements.py -v`.

### Task 4: Add frontend measurement API and pure helpers

**Files:**
- Create: `qc_frontend/src/api/measurements.js`
- Create: `qc_frontend/src/utils/measurement.js`
- Create: `qc_frontend/src/api/measurements.test.js`
- Create: `qc_frontend/src/utils/measurement.test.js`

**Interfaces:**
- `processMeasurementImage(file, calibration, options)`
- `saveMeasurementRun(payload)`
- `listMeasurementRuns()`
- `getMeasurementRun(id)`
- `deleteMeasurementRun(id)`
- `evaluateMeasurementItem(item)` and `summarizeMeasurement(items, readiness)`

- [ ] Write failing tests for FormData field names, API paths, per-item min/max/deviation, and summary precedence `REVIEW > FAIL > PASS`.
- [ ] Implement API functions using existing `client.js` conventions and multipart handling already used by inspection/quantity APIs.
- [ ] Implement frontend-only tolerance/evaluation helpers for instant UI feedback; backend remains final authority at save.
- [ ] Run focused Vitest tests.

### Task 5: Build Measurement Studio input/process/review UI

**Files:**
- Create: `qc_frontend/src/views/MeasurementStudio.vue`
- Modify: `qc_frontend/src/router/index.js`
- Modify: `qc_frontend/src/components/AppSidebar.vue`
- Modify: `qc_frontend/src/assets/locales/id.js`
- Modify: `qc_frontend/src/assets/locales/en.js`
- Create: `qc_frontend/src/views/__tests__/MeasurementStudio.test.js`

**Interfaces:**
- Route: `/measurement`.
- UI states: `empty`, `ready`, `processing`, `processed`, `evaluated`, `saved`, `error`.

- [ ] Write component tests for upload state, required calibration guard, process call, candidate rendering, and error state.
- [ ] Add a single Measurement Studio page using existing Carbon CSS variables and flat geometry.
- [ ] Add manual run name input and image upload/dropzone.
- [ ] Add calibration overlay with two draggable/clickable points and known-length input.
- [ ] Add center canvas using native SVG overlay; render candidate lines, selected geometry, calibration line, labels, and confidence/readiness state.
- [ ] Add explicit `Process measurement` action; show server result and preserve original image.
- [ ] Allow inspector to select a candidate, add a manual measurement item, and adjust endpoints.
- [ ] Add keyboard focus, visible focus states, and reduced-motion-safe feedback.
- [ ] Add bilingual labels for all new UI text.
- [ ] Run the focused component test.

### Task 6: Add per-item tolerance and evaluation UX

**Files:**
- Modify: `qc_frontend/src/views/MeasurementStudio.vue`
- Modify: `qc_frontend/src/utils/measurement.js`
- Modify: `qc_frontend/src/views/__tests__/MeasurementStudio.test.js`

- [ ] Add failing component tests for default linear/angle tolerance, per-item override, missing nominal, out-of-range FAIL, and invalid calibration REVIEW.
- [ ] Render item table with ID, label/type, measured, unit, nominal, tolerance, min, max, deviation, confidence, and status.
- [ ] Add `Set default tolerance` plus per-item override; store tolerance in item data, never globally only.
- [ ] Derive min/max from nominal and tolerance; do not accept independently conflicting limits in prototype.
- [ ] Add `Evaluate dimension` action and summary band with reason for `REVIEW`.
- [ ] Disable evaluate until process result, valid geometry, nominal, and tolerance exist.
- [ ] Run frontend tests and verify a tolerance edit updates overlay/table/status without a new process request.

### Task 7: Add save, History, reopen, and audit UX

**Files:**
- Modify: `qc_frontend/src/views/MeasurementStudio.vue`
- Modify: `qc_frontend/src/api/measurements.js`
- Modify: `qc_frontend/src/views/__tests__/MeasurementStudio.test.js`

- [ ] Write failing tests for save payload, history refresh, reopen detail, delete confirmation, and audit calls for UI actions.
- [ ] Add saved-run list in the Studio sidebar or lower panel; keep one route to avoid a separate history page in prototype.
- [ ] Save only after evaluation; show server-normalized result returned by the API.
- [ ] Reopen a saved run into read-only result state, with explicit `Edit new run` action for a fresh process.
- [ ] Add delete confirmation and refresh list after successful delete.
- [ ] Reuse `useAuditLog` for UI-only actions while avoiding duplicate server save/delete events.
- [ ] Run the complete frontend test suite.

### Task 8: Verify accuracy gate and integration

**Files:**
- Modify: `docs/PRD/Features/inspect-measurement-prototype.md` only if acceptance wording changes after evidence.
- Create or retain test fixtures under `qc_server/tests/fixtures/measurement/` only when small and necessary.

- [ ] Test `temp/output-bending_gpt.png` through the browser workflow.
- [ ] Test at least one known-scale planar sample, one rotated sample, one glare/noise sample, and one invalid-calibration sample.
- [ ] Record absolute error and repeatability; report result as evidence, not a claimed production guarantee.
- [ ] Run from `qc_server/`: `.\.venv\Scripts\python.exe -m pytest -v`.
- [ ] Run from `qc_frontend/`: `npm test` and `npm run build`.
- [ ] Run browser smoke through the existing Playwright workflow and inspect console errors.
- [ ] Confirm no CAD/PDF, camera, multi-view, or 3D behavior has leaked into prototype scope.

## Verification checklist

- Backend focused tests pass before frontend work is considered complete.
- Frontend tests cover state transitions and verdict rules, not only snapshots/text.
- Save/reopen round trip preserves calibration, geometry, tolerance, and verdict.
- Invalid calibration or ambiguous edge can never be silently shown as `PASS`.
- `git diff --check` is clean.
