# Inspect Measurement Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a one-image/one-frame, one-side, semi-automatic measurement workflow: upload, Live Camera trigger, or Mobile Camera capture → calibrate → process → review edge candidates → set per-item tolerance → evaluate → save/history/audit.

**Architecture:** Keep measurement logic server-side in a small OpenCV service. Use the existing Vue API client, Carbon layout, SQLite/SQLAlchemy, file storage, and audit router. Store one prototype run with measurement items in a JSON column; avoid a separate measurement-item table until real recipe/versioning requires relational queries.

**Tech Stack:** Vue 3, Vue Router, vanilla CSS, FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite, OpenCV headless, NumPy, Vitest, Vue Test Utils, pytest, FastAPI TestClient.

## Global Constraints

- Prototype input is image upload, one-shot Live Camera capture, or one-shot Mobile Camera capture.
- One image represents one inspected side.
- No CAD/PDF parser, continuous live measurement, multi-view session, 3D inference, trained model, or new dependency.
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

- [x] Write failing tests for px-to-mm conversion, zero/negative calibration rejection, nominal ± tolerance bounds, angle evaluation, and `REVIEW` gates.
- [x] Write failing tests for a synthetic horizontal/vertical line producing deterministic measurement output.
- [x] Implement pure math and validation without database or HTTP dependencies.
- [x] Implement candidate serialization with endpoint coordinates, pixel length, angle, confidence, and source method.
- [x] Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurement_service.py -v` from `qc_server/`.

### Task 2: Implement OpenCV candidate extraction

**Files:**
- Modify: `qc_server/app/services/measurement.py`
- Create: `qc_server/tests/test_measurement_cv.py`

**Interfaces:**
- `process_image(frame, calibration, options) -> ProcessMeasurementResult`

- [x] Add failing synthetic-image tests for a clear rectangle and a low-signal image.
- [x] Implement grayscale/denoise/edge preprocessing with existing OpenCV and NumPy only.
- [x] Use `LineSegmentDetector` first; keep `HoughLinesP` as a fallback when candidate count is insufficient.
- [x] Normalize endpoint ordering, remove short/noisy segments, deduplicate near-collinear candidates, and calculate confidence.
- [x] Return `REVIEW` readiness when no usable candidate or calibration is invalid; never fabricate a PASS measurement.
- [x] Run focused CV tests and inspect candidate coordinates against synthetic fixtures.

### Task 3: Add measurement persistence and API

**Files:**
- Modify: `qc_server/app/models.py`
- Modify: `qc_server/app/schemas.py`
- Create: `qc_server/app/routers/measurements.py`
- Modify: `qc_server/app/main.py`
- Create: `qc_server/tests/test_measurements.py`

**Interfaces:**
- `POST /api/measurements/process` — multipart `file` or `camera_id` + calibration/options; returns image metadata, source type, candidates, calibration, and readiness. Reuse existing camera registry and `grab_one()` path.
- `POST /api/measurements` — saves a named evaluated run.
- `GET /api/measurements` — lists saved runs newest first with summary fields.
- `GET /api/measurements/{run_id}` — returns complete run detail.
- `DELETE /api/measurements/{run_id}` — deletes run metadata and owned source file.
- `GET /api/measurements/files/{run_id}/{filename}` — serves contained source image.

- [x] Add failing API tests for invalid image, missing camera, unavailable camera frame, upload process response, Live Camera process response, missing calibration, save, list, detail, delete, and file serving; add path-containment guard.
- [x] Add `MeasurementRun` with manual name, timestamps, source metadata, calibration JSON, items JSON, summary verdict, and processing metadata.
- [x] Add startup directory creation and lightweight `ensure_column` migration if needed by existing SQLite databases.
- [x] Store uploaded source image under a measurement-owned directory; sanitize filenames and reject traversal.
- [x] Wire process endpoint to the measurement service without loading any trained model.
- [x] Save endpoint recomputes item limits/status server-side before persistence.
- [x] Write `MEASUREMENT_PROCESSED`, `MEASUREMENT_EVALUATED`, `MEASUREMENT_SAVED`, and `MEASUREMENT_DELETED` audit records at the corresponding server actions.
- [x] Include router in `qc_server/app/main.py`.
- [x] Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurements.py -v`.

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

- [x] Write failing tests for FormData field names, API paths, per-item min/max/deviation, and summary precedence `REVIEW > FAIL > PASS`.
- [x] Implement API functions using existing `client.js` conventions and multipart handling already used by inspection/quantity APIs.
- [x] Implement frontend-only tolerance/evaluation helpers for instant UI feedback; backend remains final authority at save.
- [x] Run focused Vitest tests.

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

- [x] Write component tests for upload state, required calibration guard, process call, candidate rendering, and error state.
- [x] Add a single Measurement Studio page using existing Carbon CSS variables and flat geometry.
- [x] Add manual run name input, image upload/dropzone, Live Camera selector, existing MJPEG preview, `Trigger capture`, and Mobile Camera `getUserMedia()` capture action.
- [x] Add calibration overlay with reference points and known-length input.
- [x] Add center canvas using native SVG overlay; render candidate lines, selected geometry, calibration line, labels, and confidence/readiness state.
- [x] Add explicit `Process measurement` action; show server result and preserve original image/frame plus source type.
- [x] Allow inspector to select a candidate, add a manual measurement item, and adjust measurement inputs.
- [x] Add keyboard focus, visible focus states, and reduced-motion-safe feedback.
- [x] Add bilingual labels for all new UI text.
- [x] Run the focused component test.

### Task 6: Add per-item tolerance and evaluation UX

**Files:**
- Modify: `qc_frontend/src/views/MeasurementStudio.vue`
- Modify: `qc_frontend/src/utils/measurement.js`
- Modify: `qc_frontend/src/views/__tests__/MeasurementStudio.test.js`

- [x] Add failing component tests for default linear/angle tolerance, per-item override, missing nominal, out-of-range FAIL, and invalid calibration REVIEW.
- [x] Render item table with ID, label/type, measured, unit, nominal, tolerance, min, max, deviation, confidence, and status.
- [x] Add default linear tolerance plus per-item override; store tolerance in item data, never globally only.
- [x] Derive min/max from nominal and tolerance; do not accept independently conflicting limits in prototype.
- [x] Add `Evaluate dimension` action and summary band with reason for `REVIEW`.
- [x] Disable evaluate until process result, valid geometry, nominal, and tolerance exist.
- [x] Run frontend tests and verify a tolerance edit updates overlay/table/status without a new process request.

### Task 7: Add save, History, reopen, and audit UX

**Files:**
- Modify: `qc_frontend/src/views/MeasurementStudio.vue`
- Modify: `qc_frontend/src/api/measurements.js`
- Modify: `qc_frontend/src/views/__tests__/MeasurementStudio.test.js`

- [x] Write failing tests for save payload, history refresh, reopen detail, delete confirmation, and audit calls for UI actions.
- [x] Add saved-run list with search in the Studio sidebar; keep one route to avoid a separate history page in prototype.
- [x] Save only after evaluation; show server-normalized result returned by the API.
- [x] Reopen a saved run into read-only result state.
- [x] Add delete confirmation and refresh list after successful delete.
- [x] Reuse `useAuditLog` for UI-only actions while avoiding duplicate server save/delete events.
- [x] Run the complete frontend test suite.

### Task 8: Verify accuracy gate and integration

**Files:**
- Modify: `docs/PRD/Features/inspect-measurement-prototype.md` only if acceptance wording changes after evidence.
- Create or retain test fixtures under `qc_server/tests/fixtures/measurement/` only when small and necessary.

- [ ] Test `temp/output-bending_gpt.png` through the browser workflow.
- [x] Mock a registered Live Camera, trigger one frame, and run that frame through the same process/evaluate/save flow.
- [x] Verify Mobile Camera source metadata and client capture controls.
- [ ] Test at least one known-scale planar sample, one rotated sample, one glare/noise sample, and one invalid-calibration sample.
- [ ] Record absolute error and repeatability; report result as evidence, not a claimed production guarantee.
- [x] Run from `qc_server/`: `.\.venv\Scripts\python.exe -m pytest -v`.
- [x] Run from `qc_frontend/`: `npm test -- --run --maxWorkers=1` and `npm run build`.
- [x] Run browser smoke through the existing Playwright workflow and inspect console errors.
- [x] Confirm no CAD/PDF, multi-view, or 3D behavior has leaked into prototype scope.

## Verification checklist

- Backend focused tests pass before frontend work is considered complete.
- Frontend tests cover state transitions and verdict rules, not only snapshots/text.
- Save/reopen round trip preserves calibration, geometry, tolerance, and verdict.
- Invalid calibration or ambiguous edge can never be silently shown as `PASS`.
- `git diff --check` is clean.
