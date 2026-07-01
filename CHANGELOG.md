# CHANGELOG

> **Agent Memory Contract.** This file is the single source of truth for what changed, when, and why. Every AI agent working on this repo MUST read this file before starting work and MUST append an entry after committing changes. See `AGENTS.md` section "Documentation Maintenance" for the full contract.

All notable changes to the MQC-AI project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [Semantic Versioning](https://semver.org/).

Each entry contains:
1. Standard Keep a Changelog categories (Added / Changed / Fixed / Removed)
2. **Current Codebase State** table tracing what was developed and the resulting state

---

## [Unreleased] - 2026-07-01 - QC Studio SAM Click-to-Segment

### Summary

QC Studio edit mode now supports SAM-assisted point and box annotation. Inspectors can click a defect or drag a box, receive a simplified SAM polygon, choose an enabled defect class, and save it through the existing manual defect endpoint.

### Added

- `qc_server/app/services/inference/sam_interactive.py` - lazy Ultralytics `SAM` loader cached by model path, highest-confidence mask selection, and `simplify_polygon()` reuse for point/box prompts.
- `POST /api/batches/{batch_id}/images/{image_id}/segment` - validates exactly one point or box prompt, resolves `qc_model`, checks image ownership, and returns `{ polygon }`.
- `qc_server/tests/test_segment.py` - mocked-SAM endpoint coverage for point, box, prompt validation, missing model, and ownership 404s.
- `qc_frontend/src/api/batches.js` - `segmentDefect()` API helper with unit coverage.
- `InspectionCanvas.vue` - edit dock SAM point and SAM box tools, segmenting hint, box preview rectangle, empty-result message, and class-picker reuse.
- `qc_frontend/src/utils/canvasCoords.js` - tested `normalizeBox()` helper for box drag directions.
- `qc_frontend/src/assets/locales/en.js` and `id.js` - SAM tool labels, hints, loading state, and empty-result copy.

### Changed

- QC Studio suspends pan while SAM tools are active and uses the existing pending-polygon class picker plus Phase-1 `addDefect()` flow after SAM returns a polygon.
- SAM-added defects log through the existing `DEFECT_ADDED` audit action after the inspector picks a class.
- Manual polygon draw remains the fallback annotation path.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Interactive SAM backend | 2026-07-01 | Lazy SAM service plus per-image segment endpoint for point/box prompts | Laptop tests run without Ultralytics imports; configured `qc_model` drives real SAM on the GPU server. |
| QC Studio assisted annotation | 2026-07-01 | SAM point and SAM box tools feed returned polygons into the existing class-picker/save flow | Inspectors can create AI-assisted defects in Edit mode while manual draw/delete/relabel still work. |
| Verification | 2026-07-01 | Backend full suite, frontend full suite, and production build | Backend: 117 passed, 2 warnings. Frontend: 66 passed. Build succeeded. |

### Notes

- Real SAM segmentation smoke is deferred to the reviewer on the GPU server: point quality/latency, box quality/latency, empty background response, and Phase-1 edit regression checks.
- No new dependency was added; SAM remains in `qc_server/requirements-ml.txt`.

## [Unreleased] - 2026-07-01 - QC Studio Edit-Mode UX

### Summary

QC Studio edit mode now behaves more like a focused annotation tool: canvas controls float over the work area, defect selection is shared between the canvas and defect panel, cursors match the active interaction, and core actions have keyboard shortcuts.

### Added

- `qc_frontend/src/utils/cursor.js` and `cursor.test.js` - pure `cursorForState()` helper covering drawing, dragging, polygon hover, and default pan cursors.
- `qc_frontend/src/composables/useInspection.js` - shared `selectedDefectId`, `selectDefect()`, and `clearDefectSelection()` state for canvas/panel selection.
- `InspectionCanvas.vue` - edit-only left tool dock, top-right annotation/review/View|Edit cluster, bottom-right zoom cluster, drawing hint, and keyboard shortcuts for V/A/Delete/Esc/+/-/0.
- `DefectPanel.vue` - click/keyboard row selection with active row styling and shared selection highlighting.

### Changed

- `InspectionCanvas.vue` replaces the crowded single toolbar with flat Carbon-style floating clusters and reduced-motion-safe dock entry motion.
- Canvas polygons can be selected in both View and Edit modes; selected polygons render stronger than hover.
- `DefectPanel.vue` active rows use full-border/background state instead of side-stripe accents.
- `qc_frontend/src/assets/locales/en.js` and `id.js` include new edit-tool labels, View/Edit labels, annotation state labels, and drawing hint copy.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| QC Studio floating controls | 2026-07-01 | Split the canvas controls into edit dock, top action cluster, and zoom cluster | Canvas work area is less crowded while retaining review, annotation, edit-mode, and zoom actions. |
| Defect selection | 2026-07-01 | Shared `selectedDefectId` in `useInspection()` and row/polygon click handlers | Clicking a defect row highlights its polygon, and clicking a polygon highlights the row in View and Edit modes. |
| Cursor/shortcut UX | 2026-07-01 | Tested `cursorForState()` plus V/A/Delete/Esc/+/-/0 shortcuts that ignore typing targets | Operators get predictable cursor feedback and fast keyboard access to common annotation actions. |
| Verification | 2026-07-01 | Frontend focused red/green, full suite, and production build | Focused red: missing `cursor.js` module. Focused green: 4 passed. Full frontend: 64 passed. Build succeeded. |

### Notes

- Phase 2 (SAM click-to-segment with point/box prompts) remains next and can add tools to the new left dock.
- Browser smoke is pending for reviewer: floating docks + pan-under, bidirectional selection both modes, cursor per tool, drawing hint, keyboard shortcuts, and Phase 1 add/delete/relabel/persist regression check.

## [Unreleased] - 2026-07-01 - QC Studio Manual Defect Editing

### Summary

QC Studio now has a default view-only mode plus an opt-in edit mode for human-in-the-loop defect correction. Inspectors can draw manual defect polygons, delete false positives, and relabel defect classes without a schema migration or ML changes.

### Added

- `qc_server/app/routers/batches.py` - nested defect CRUD endpoints: `POST/PATCH/DELETE /api/batches/{batch_id}/images/{image_id}/defects[/{defect_id}]`.
- `qc_server/app/schemas.py` - `DefectCreate` and `DefectPatch` request schemas.
- `qc_server/tests/test_batches.py` - backend CRUD coverage for create/patch/delete status/count recompute and ownership 404s.
- `qc_frontend/src/utils/canvasCoords.js` and `canvasCoords.test.js` - pure `toImageCoords()` helper for SVG pointer-to-image coordinate mapping.
- `qc_frontend/src/api/batches.js` - `createDefect`, `updateDefect`, and `deleteDefect` API helpers with wrapper tests.
- QC Studio edit-mode controls in `InspectionCanvas.vue` and `DefectPanel.vue`, backed by `useInspection()` local state updates and audit actions.

### Changed

- `qc_frontend/src/composables/useInspection.js` now persists edit mode in `localStorage` key `mqc-edit-mode` and exposes add/update/remove defect methods.
- `InspectionCanvas.vue` supports polygon drawing with pan suspended while drawing, class picking from enabled defect classes, Esc cancel, click-to-select, and Delete/delete-button removal.
- `DefectPanel.vue` shows delete and relabel controls only in edit mode; view-only mode remains read-only.
- `qc_frontend/src/assets/locales/en.js` and `id.js` include edit-mode labels and `DEFECT_ADDED` / `DEFECT_DELETED` / `DEFECT_RELABELED` audit labels.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Backend defect editing API | 2026-07-01 | Nested create/update/delete defect endpoints with image ownership checks and status/count recompute | Manual corrections persist in SQLite and update image status plus batch defect counts without changing reviewed state. |
| QC Studio edit mode | 2026-07-01 | View-only default plus persisted edit mode, draw-to-add, delete, and relabel UI | Inspectors can correct SAM/mock results directly in QC Studio while normal review/export stays unchanged by default. |
| Coordinate mapping | 2026-07-01 | Tested `toImageCoords()` using SVG rect math for zoom/pan-safe pointer mapping | Drawn polygon points are stored in image pixel coordinates. |
| Verification | 2026-07-01 | Backend full suite, frontend full suite, and production build | Backend: 112 passed, 2 warnings. Frontend: 60 passed. Build succeeded. |

### Notes

- Phase 2 (SAM click-to-segment with point/box prompts) remains planned for a separate later branch.
- Browser smoke is pending for reviewer: view-only default, toggle Edit, draw/add defect and pick class, delete, relabel, persistence after reload, and edit-mode persistence in localStorage.

## [Unreleased] - 2026-07-01 - Audit Report PDF Defect Crops

### Summary

Reports PDF generation now embeds annotated per-defect crop images grouped by inspected image while keeping all report text as jsPDF vector text.

### Added

- `qc_frontend/src/utils/export.js` - shared `loadImage(url)` image loader and pure `fitDimensions(srcW, srcH, maxW, maxH)` aspect-ratio helper.
- `qc_frontend/src/utils/export.test.js` - unit coverage for `fitDimensions` width clamp, height clamp, unchanged small boxes, and aspect-ratio preservation.
- `qc_frontend/src/views/Reports.vue` - visual Defect Details PDF section with filename headers, defect counts, annotated crop PNG embeds, captions, wrapping rows, page breaks, and clean-batch fallback.

### Changed

- `qc_frontend/src/views/Reports.vue` removes the artificial PDF generation delay and reuses `renderAnnotated`, `defectCropBox`, `renderDefectCrop`, and `useDefectColor().colorFor` so report crops match Export Crop colors.
- `qc_frontend/src/components/DefectPanel.vue` now imports the shared `loadImage()` helper instead of keeping a duplicate local image loader.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Reports PDF defect details | 2026-07-01 | Grouped-by-image annotated defect crops embedded with `doc.addImage()` while text stays `doc.text()` vector output | Audit PDFs show visual crop evidence per defect without rasterizing the full report. |
| Export utilities | 2026-07-01 | Shared image loader and tested aspect-ratio fit helper | Reports and DefectPanel reuse one image-loading path; crop print sizing is unit-tested. |
| Verification | 2026-07-01 | Frontend focused red/green, full suite, and production build | Focused red: 4 expected `fitDimensions is not a function` failures; focused green: 12 passed. Full frontend: 54 passed. Build succeeded. |

### Notes

- Browser smoke is pending for reviewer: generate a PDF for a batch with defects and verify crops grouped by image, class-color annotations, captions, vector/crisp text, multi-page pagination, signature block, and clean-batch PDF behavior.

## [Unreleased] - 2026-07-01 - Media Detection Multi-Image Upload

### Summary

Media Detection image mode now stages multiple images. Test mode runs object detection once per image and Process to QC sends all uploaded images through one backend crop session, one crop-review dialog, and one QC batch.

### Added

- `qc_server/app/routers/detect.py` - `POST /api/detect/image/process` now accepts multipart `files` and appends crops from every valid uploaded image into one media crop session.
- `qc_frontend/src/api/detect.js` - `processImages(files)` posts each image under the `files` field while keeping `processImage(file)` as a one-file wrapper.
- `qc_frontend/src/views/MediaDetection.vue` - multi-image staged upload list with per-row remove, clear all, add more, per-image Test result cards, and combined Process-to-QC review.
- Backend and frontend tests for multi-image process sessions, single-image list compatibility, invalid-image rejection, staged list behavior, video single-file behavior, and per-image Test detection.

### Changed

- Media Detection image upload input is `multiple`; video upload remains single-file.
- Image Process-to-QC now collects crops across all selected images before review and approval.
- New locale strings in both `en.js` and `id.js` for add-more, clear-all, and selected-count UI.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Media Detection image staging | 2026-07-01 | `selectedFiles` list, add more, clear all, per-row remove, preview URL cleanup | Operators can stage multiple images in image mode while video mode still keeps one file. |
| Image Test flow | 2026-07-01 | Test mode loops `detectImage()` per staged image and renders one result card per image | Multi-image test runs are visible as separate annotated results. |
| Image Process-to-QC flow | 2026-07-01 | `processImages()` posts multipart `files`; backend creates one crop session and finalizes once | Crops from all uploaded images enter one review dialog and one submitted QC batch. |
| Verification | 2026-07-01 | Backend full suite, frontend full suite, and production build | Backend: 110 passed, 2 warnings. Frontend: 50 passed. Build succeeded. |

### Notes

- Browser/GPU smoke is pending for reviewer: drop 3 images, run Test and Process flows with a configured model, approve crops, verify one QC batch, and confirm video mode still accepts one file.

## [Unreleased] - 2026-07-01 - QC Studio Batch Export (Crop + Full)

### Summary

QC Studio's DefectPanel export buttons now operate on the whole loaded batch and use the same `DefectClass.color` source as the on-screen canvas (`useDefectColor().colorFor`), replacing a dead CSS-variable color lookup that always rendered grey.

### Added

- `qc_frontend` dependency: `jszip` for client-side ZIP packaging of multi-file exports.
- `qc_frontend/src/utils/export.js` - `stripExt`, `fullFilename`, `cropFilename`, `defectCropBox`, `renderDefectCrop`, `canvasToBlob`, `downloadBlob` pure/canvas helpers.
- `qc_frontend/src/utils/export.test.js` - unit coverage for the new pure helpers (naming + bbox padding/clamping).

### Changed

- `qc_frontend/src/utils/export.js` `renderAnnotated(imgEl, image, colorFor)` now takes a color resolver instead of resolving a dead `--defect-{type}` CSS variable; `DefectPanel.vue` passes `useDefectColor().colorFor`.
- `qc_frontend/src/components/DefectPanel.vue` `exportFull()`/`exportCrop()` now iterate every image (and every defect) in the loaded batch instead of only the selected image; more than one output file packages into a `jszip` archive (`{batchName}_full.zip` / `{batchName}_crops.zip`), exactly one output downloads as a single PNG.
- `qc_frontend/src/views/Reports.vue` defect tag colors now source from `useDefectColor().colorFor` instead of the removed `utils/defect.js` `defectColor`.

### Removed

- `qc_frontend/src/utils/export.js` `resolveColor` (dead CSS-var lookup) and `defectsBBox` (superseded by per-defect `defectCropBox`).
- `qc_frontend/src/utils/defect.js` `COLOR_MAP` and `defectColor` (dead CSS-var lookup; the `DefectClass.color`/`useDefectColor()` path is now the only color source).

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Batch export colors | 2026-07-01 | `renderAnnotated` takes an injected `colorFor` resolver | Export Full/Crop annotation colors match the on-screen canvas and Settings-configured `DefectClass.color`. |
| Whole-batch export | 2026-07-01 | Export Full/Crop iterate every image/defect in the loaded batch, ZIP via `jszip` when >1 file | Operators export the entire batch in one action instead of only the selected image. |
| Reports color source | 2026-07-01 | `Reports.vue` defect tags use `useDefectColor()` | Report preview colors also stop reading the dead CSS variable. |
| Verification | 2026-07-01 | Frontend full suite and production build | Frontend: 47 passed. Build succeeded. |

### Notes

- Deviation from plan: the plan stated `utils/defect.js` `defectColor`/`COLOR_MAP` had no importers, but `Reports.vue` did import and use `defectColor` for its defect tag colors. Updated that call site to `useDefectColor().colorFor` (same fix as the export color bug) instead of leaving a broken import, per the plan's own contingency note ("Reports/PDF may use them").
- Browser smoke is pending for reviewer: Export Full (multi-image ZIP + single-image PNG), Export Crop (multi-defect ZIP + single-defect PNG + no-defects message), and colors matching Settings on a real batch with a running `qc_server` + browser.

## [Unreleased] - 2026-06-30 - QC Workflow Raw Images, Delete, Confidence, Colors, Re-run

### Summary

QC Studio now opens pending batches with raw image rows already visible, supports deleting an image and its source crop file, uses a dedicated QC confidence setting separate from object detection, colors annotations from configured defect-class colors, and can re-run or reset finished batches.

### Added

- `qc_server/app/services/pipeline.py` - `prepare_images()` pre-creates raw `Image` rows from the submitted crop folder and `run_batch()` now updates those rows instead of creating replacements.
- `DELETE /api/batches/{batch_id}/images/{image_id}` - removes a batch image row, cascades defects, deletes the underlying crop file, and updates `image_count`.
- `Setting.qc_confidence_threshold` with startup migration and settings API schema support.
- `qc_frontend/src/composables/useDefectColor.js` - resolves annotation and panel swatch colors from `DefectClass.color`.
- QC Studio image delete control with confirmation and `IMAGE_DELETED` audit label.
- `POST /api/batches/{batch_id}/reset` plus QC Studio **Re-run** and **Reset** controls.

### Changed

- `POST /api/batches` now leaves batches `pending` but pre-populates image rows with `status="pending"` and no defects, so QC Studio can show the raw list/canvas before segmentation.
- Batch segmentation defaults to `qc_confidence_threshold`; live/media object detection keeps using `confidence_threshold`.
- Settings relabels the original threshold as **Object Detection Confidence** and adds **QC Confidence**.
- `QcRunDialog` defaults its confidence input from `settings.qcConfidenceThreshold`.
- `InspectionCanvas.vue` and `DefectPanel.vue` use configured defect-class colors instead of the old hardcoded four-entry defect map.
- `POST /api/batches/{batch_id}/run` now allows finished/failed/reviewed batches and rejects only currently processing batches.
- Re-running or resetting clears stale defect results and local reviewed marks.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Pending batch raw state | 2026-06-30 | Batch submit pre-creates pending image rows; pending QC Studio loads raw images without polling | Operators can inspect the submitted crop set before running SAM 3 segmentation. |
| Image delete | 2026-06-30 | Backend image delete endpoint plus QC Studio per-image delete control and audit label | Operators can permanently remove a bad crop from a pending/loaded batch before any run. |
| QC confidence | 2026-06-30 | `qc_confidence_threshold` DB/API/frontend setting and dialog default | Object detection and QC segmentation confidence can be tuned independently. |
| Defect colors | 2026-06-30 | `useDefectColor()` maps defect type names to `DefectClass.color` | QC polygons and panel swatches match the colors configured in Settings. |
| Re-run/reset | 2026-06-30 | Run endpoint relaxed; reset endpoint and QC Studio controls added | Finished batches can be segmented again or returned to the pending raw state. |
| Verification | 2026-06-30 | Backend full suite and frontend full suite/build | Backend: 107 passed; frontend: 44 passed; build succeeded. |

### Notes

- Browser/GPU smoke is pending for reviewer: pending raw list, image delete file removal, Load Batch colors matching Settings, QC confidence independence, and re-run/reset UI flow.

## [Unreleased] - 2026-06-30 - SAM 3 Prompt Strategy

### Summary

Batch QC now has a real `sam3_prompt` defect strategy that uses Ultralytics SAM 3 text-concept prompts from enabled defect classes. Settings now keeps the live object-detection model and QC segmentation model separate via `active_model` and `qc_model`.

### Added

- `qc_server/app/services/inference/sam3.py` - lazy `SAM3SemanticPredictor` seam, `Sam3Strategy`, pure-Python Ramer-Douglas-Peucker polygon simplifier, mask polygon clamping, and `"sam3_prompt"` registration.
- `qc_server/app/models.py`, `qc_server/app/main.py`, and `qc_server/app/schemas.py` - `Setting.qc_model` field, guarded startup migration, and settings API schema support.
- `qc_server/tests/test_qc_model_setting.py`, `qc_server/tests/test_sam3_strategy.py`, and `qc_server/tests/test_pipeline_sam3.py` - unit coverage for settings persistence, no-ML SAM3 strategy behavior, polygon simplification, and pipeline `qc_model_path` plumbing.
- `qc_frontend/src/views/Settings.vue` - **QC / Segmentation Model** dropdown using the existing `.pt` model list.

### Changed

- `qc_server/app/services/pipeline.py` now imports the SAM3 strategy registration, resolves `qc_model` against `settings.models_dir`, and passes `qc_model_path` into defect strategies.
- `qc_server/requirements-ml.txt` now requires `ultralytics>=8.3.237,<9` for SAM 3 support.
- `qc_frontend/src/api/settings.js` maps `qc_model` to/from `qcModel`.
- `qc_frontend/src/assets/locales/en.js` and `qc_frontend/src/assets/locales/id.js` relabel the existing active model as the object-detection model and add QC model text.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| SAM3 defect inference | 2026-06-30 | `sam3_prompt` strategy with lazy SAM 3 predictor, per-enabled-class text prompts, confidence filtering, and polygon simplification | Batch QC can run real SAM 3 prompt segmentation when the strategy and QC model are configured. |
| QC model setting | 2026-06-30 | `qc_model` DB field, migration, schemas, API mapping, and Settings dropdown | Live object detection keeps using `active_model`; batch QC segmentation uses separate `qc_model`. |
| Pipeline plumbing | 2026-06-30 | Pipeline resolves `qc_model_path` and passes it to strategies | `mock` ignores the extra param; `sam3_prompt` fails loudly if no QC model is selected. |
| Verification | 2026-06-30 | Backend full suite, frontend full suite, and production build | Backend: 99 passed, 2 warnings. Frontend: 39 passed. Build succeeded. |

### Notes

- Real-weight GPU smoke (Task 7) is deferred to the reviewer/local server with `sam3.pt` in `qc_server/models/`.
- Unit tests monkeypatch the predictor seam; no `ultralytics` or `torch` import is required for laptop tests.

## [Unreleased] - 2026-06-30 - Defect Class Management

### Summary

Defect classes now have a comprehensive coating+welding seed set, idempotent startup seeding for existing databases, optional auto-generated create IDs, and a compact Settings management UI for enabling, adding, editing, and deleting classes.

### Added

- `qc_server/app/services/seed.py` - expanded canonical defect classes to 25 coating+welding variants with enabled defaults and idempotent add-missing-by-id seeding.
- `qc_server/app/schemas.py` and `qc_server/app/routers/defect_classes.py` - `DefectClassCreate` lets `POST /api/defect-classes` omit `id`; the server slugifies `name` to `dc-*` and suffixes duplicates.
- `qc_frontend/src/api/defectClasses.js` and `qc_frontend/src/composables/useDefectClasses.js` - live defect-class API helpers and singleton composable.
- `qc_frontend/src/components/DefectClassModal.vue` - add/edit modal with name, category, and swatch color selection.
- `qc_frontend/src/views/Settings.vue` - Defect Classes section grouped by coating/welding with enabled counts, toggles, add/edit, and delete confirmation.
- `qc_frontend/src/views/__tests__/DefectClasses.test.js` - component coverage for grouped counts, toggles, add, and delete confirmation.

### Changed

- `POST /api/defect-classes` keeps explicit `id` creation working, but `id` is now optional for UI-created classes.
- Settings now configures which defect classes future SAM 3 prompt-based batches should inspect.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Defect class seed | 2026-06-30 | 25 canonical coating+welding defect variants and add-missing-by-id seeding | Existing DBs gain new canonical classes without overwriting user edits. |
| Defect class API | 2026-06-30 | Optional-id create with slug generation and duplicate suffixes | Operators can add classes without hand-writing stable IDs; explicit IDs still work. |
| Settings UI | 2026-06-30 | Grouped Defect Classes section with counts, enable toggles, add/edit modal, and delete confirmation | Enabled class configuration is manageable from the dashboard and ready for SAM 3 Part B prompts. |
| Verification | 2026-06-30 | Backend full suite, frontend full suite, and production build | Backend: 90 passed, 2 warnings. Frontend: 37 passed. Build succeeded. |

### Notes

- Browser smoke is pending for reviewer: grouped list/counts, toggle persistence, add auto-ids, edit/delete, and idempotent seed on an existing DB.
- Deviation from plan test text: auto-id tests use `custom flaw` because `orange peel` is now seeded canonically and would correctly dedupe on startup.
- Real `sam3_prompt` inference remains deferred to SAM 3 MVP Part B.

## [Unreleased] - 2026-06-30 - Crop Quality (Lossless PNG + Padding)

### Summary

Defect object crops are now saved as lossless PNG files with about 5% bbox padding, preserving fine defect texture and reducing clipped-edge crops across Live Monitor and Media Detection crop paths.

### Changed

- `qc_server/app/services/crop.py` - `crop_objects()` now pads scaled bounding boxes by `pad_frac=0.05`, clamps to frame bounds, skips zero-area boxes before padding, writes `obj_NNN.png`, and keeps existing callers compatible.
- `qc_server/app/routers/cameras.py` and `qc_server/app/routers/detect.py` - crop serving now uses `FileResponse(path)` so Starlette infers `image/png` from the filename instead of hardcoding `image/jpeg`.
- `qc_server/tests/test_crop.py` and `qc_server/tests/test_crop_session.py` - crop tests now assert PNG filenames, scaled padding, clamped padding, and accumulated session filenames.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Crop writer | 2026-06-30 | Shared `crop_objects()` changed from tight JPEG boxes to padded PNG crops | Auto, Manual, and Media Detection crop paths produce lossless `obj_NNN.png` files with small context margins. |
| Crop serving | 2026-06-30 | Camera/media crop endpoints infer response content type from the saved file | PNG crop thumbnails are served as `image/png` without route-specific media-type drift. |
| Verification | 2026-06-30 | Backend full suite, frontend full suite rerun, and production build | Backend: 87 passed, 2 warnings. Frontend: 34 passed after one transient BatchHistory timeout rerun. Build succeeded. |

### Notes

- Crops already came from original full-resolution frames; this change improves encoding and bbox margins, not camera capture resolution.
- Reduced crop padding from 8% to 5% per side (SAM 3 best practice: small margin, subject dominant).
- Clamp-test integer asserted: `21` pixels for a top-left `20x20` box with `pad_frac=0.05` because `round(21.0)=21`.
- Real `sam3_prompt` segmentation remains deferred to M4.
- Manual smoke is pending for reviewer: confirm `obj_NNN.png`, visible margin/sharpness, and `image/png` thumbnails in browser flows.

## [Unreleased] - 2026-06-30 - Batch Delete + Sidebar Logo

### Summary

Batch History can now delete batches through a backend `DELETE /api/batches/{id}` endpoint with a confirmation dialog in the dashboard. The sidebar brand lockup now displays `GSPE | MQC-AI` when expanded and centers `GSPE` when collapsed.

### Added

- `DELETE /api/batches/{batch_id}` - deletes the batch, its images, defects, and `data/batches/<batch_id>/` result directory while leaving source crop folders untouched.
- `qc_frontend/src/api/batches.js` - `deleteBatch(batchId)` helper using the existing `apiDelete`.
- `qc_frontend/src/composables/useBatchHistory.js` - `remove(id)` deletes a batch and removes it from loaded state.
- `qc_frontend/src/views/BatchHistory.vue` - Delete action with confirm/cancel dialog and error display.
- `qc_frontend/src/views/__tests__/BatchHistory.test.js` - component coverage for delete confirmation.

### Changed

- `qc_frontend/src/components/AppSidebar.vue` - refined sidebar wordmark to `GSPE | MQC-AI` expanded and centered `GSPE` collapsed.
- `qc_frontend/src/assets/locales/en.js` and `qc_frontend/src/assets/locales/id.js` - added Batch History delete dialog strings.

### Fixed

- Batch History delete confirmation now renders as a centered modal overlay instead of an inline block that expanded the page (the `.dialog-overlay`/`.dialog` classes were not global).

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Batch deletion API | 2026-06-30 | `DELETE /api/batches/{batch_id}` with image/defect cleanup and result directory removal | Operators can remove obsolete processed batches without deleting source crop folders. |
| Batch History UI | 2026-06-30 | Delete button, confirmation modal, local row removal, and component test | Batch deletion is explicit and confirmed via a centered modal. |
| Sidebar branding | 2026-06-30 | Expanded `GSPE | MQC-AI` lockup and collapsed centered `GSPE` | The collapsed sidebar no longer clips or left-aligns the brand mark. |
| Verification | 2026-06-30 | Backend full suite, frontend full suite, and production build | Backend: 82 passed, 2 warnings. Frontend: 28 passed. Build succeeded. |

### Notes

- Browser smoke confirmed by the reviewer: delete confirm/cancel flow and collapsed sidebar centering.

## [Unreleased] - 2026-06-30 - Media Detection Production Upload UI

### Summary

Media Detection now behaves like a production CV upload tool: drag-and-drop staging, explicit Run trigger, active-model context, progress feedback, confidence-bar results, and complete upload/error/no-model states. The Media Detection navigation item is always visible, and the Settings page toggle was removed while leaving the backend `input_mode_enabled` field vestigial.

### Added

- `PRODUCT.md` - strategic product context required by the `impeccable` design workflow.
- `.impeccable/live/config.json` - live-mode config for the Vite shell.
- Media Detection staged upload state: selected file preview, drag-over state, invalid-type messaging, no-model disabled state, and active-model strip.
- Media Detection unit coverage for staging without auto-processing, invalid types, Process-to-QC review, approve/submit routing, and no-model run guard.

### Changed

- `qc_frontend/src/views/MediaDetection.vue` - rewritten around drag-and-drop upload, staged file preview, explicit Run detection action, image/video Test mode, Process-to-QC crop review, video progress bar, and per-detection confidence bars.
- `qc_frontend/src/components/AppSidebar.vue` - Media Detection nav item is unconditional.
- `qc_frontend/src/views/Settings.vue` - removed the "Enable Media Detection page" checkbox and save handler.
- `qc_frontend/src/assets/locales/en.js` and `qc_frontend/src/assets/locales/id.js` - added production upload strings and removed the unused Settings toggle label.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Media Detection upload UX | 2026-06-30 | Drag-and-drop zone, staged preview, explicit Run trigger, active-model strip, progress, confidence bars, and no-model/error states | Operators can stage media safely and run active-model detection only when ready. |
| Media Detection navigation | 2026-06-30 | Sidebar entry made unconditional; Settings toggle removed | Media Detection is always available in the dashboard. |
| Settings input mode | 2026-06-30 | Frontend usage removed; backend field left untouched | `input_mode_enabled` remains vestigial for compatibility. |
| Verification | 2026-06-30 | Frontend full suite, production build, and backend regression suite | Frontend: 33 passed. Build succeeded. Backend: 84 passed, 2 warnings. |

### Notes

- Supersedes the earlier UX-refinements plan; the Run trigger is included here.
- Deviation: `useI18n.t()` does not support `{var}` interpolation, so invalid-type and frame labels use plain translated strings plus JS composition instead of `{kind}` / `{done}` / `{total}` placeholders.
- Browser smoke is pending for reviewer: drag/drop, staged preview, Run trigger, invalid-type, progress, no-model disabled, empty detections, and Settings no-toggle checks.

## [Unreleased] - 2026-06-29 - Media Detection Crop-to-QC

### Summary

Detection Test is now Media Detection with separate Test and Process to QC modes. Process mode crops detected objects from uploaded images synchronously, extracts video crops asynchronously with the existing presence-cycle counter, and sends selected crops through the shared review-and-approve QC batch flow.

### Added

- `qc_server/app/services/detect_extract.py` - async uploaded-video crop extraction using `PresenceCounter`, `job_queue`, and injectable `capture_factory` for tests.
- `POST /api/detect/image/process` - sync uploaded-image object crop export.
- `POST /api/detect/video/{video_id}/extract` and `GET /api/detect/video/{video_id}/extract/status` - async uploaded-video crop extraction and polling.
- `GET /api/detect/crop-session/{key}`, `POST /api/detect/crop-session/{key}/approve`, and `GET /api/detect/crops/{key}/{session_ts}/{filename}` - media crop review, approval, and thumbnail serving.
- `qc_frontend/src/components/CropReviewDialog.vue` - shared crop review dialog used by Live Monitor and Media Detection.
- `qc_frontend/src/views/MediaDetection.vue` - Test/Process upload workflow with image/video support and crop-to-QC submission.
- Frontend and backend tests for media crop endpoints, video extraction, shared crop review, and Media Detection process/test modes.

### Changed

- Detection Test route/view/nav labels renamed to Media Detection (`/media-detection`, route name `media`) while keeping the `input_mode_enabled` setting key and `/api/detect/*` backend prefix.
- Live Monitor now uses `CropReviewDialog` instead of its inline crop approval dialog.
- `qc_server/app/services/crop_session.py` exposes shared `approve_session()` and `crop_file_path()` helpers reused by camera and media routers.
- Settings copy now describes the gated page as Media Detection.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Media Detection page | 2026-06-29 | `/media-detection` with Test and Process to QC modes | Operators can test annotated uploads or process uploaded media into QC batches. |
| Image crop export | 2026-06-29 | `POST /api/detect/image/process` crop-all flow | Uploaded images produce object crop URLs immediately for review. |
| Video crop extraction | 2026-06-29 | Background extraction job using `PresenceCounter` and polling progress | Uploaded videos produce one crop per debounced object presence cycle. |
| Crop review dialog | 2026-06-29 | Shared `CropReviewDialog.vue` | Live Monitor and Media Detection approve selected crop thumbnails through one UI component. |
| Verification | 2026-06-29 | Backend full suite, frontend full suite, and production build | Backend: 84 passed. Frontend: 31 passed. Build succeeded. |

### Notes

- GPU + model + browser smoke is deferred to the server: Media Detection Test image preview, Process image review to QC, Process video progress/review to QC, and Settings page gate remain pending.
- Deviation: `CropReviewDialog` watches both `show` and `crops` so it handles Live Monitor's async finalize flow where the dialog opens before crop URLs return.

## [Unreleased] - 2026-06-29 - Auto Presence-Cycle Crop

### Summary

Auto mode now crops one best-frame image per physical object using a debounced presence cycle. This fixes zero crops on single-mode cameras and avoids re-entry double-counting for workers presenting parts one at a time.

### Added

- `qc_server/app/services/presence_counter.py` - `PresenceCounter` state machine for present/absent debounce, cumulative count, best-confidence frame selection, and one crop per confirmed object.
- `qc_server/app/services/annotated_stream.py` - optional `counter` callback for annotated MJPEG streams.
- `qc_server/tests/test_presence_counter.py` - coverage for debounce, re-entry, flicker, tiny-detection filtering, and best-frame selection.

### Changed

- `qc_server/app/routers/cameras.py` Auto `detect-stream` now uses `PresenceCounter` bound to the active crop session.
- Auto count is now a cumulative presence count returned through `/api/cameras/{camera_id}/count`.
- `annotated_mjpeg()` bypasses ByteTrack and `crop_sink` when a `counter` callback is provided.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Auto crop mode | 2026-06-29 | Presence-cycle counter with best-frame crop on confirmation | Workers can present parts one at a time; each confirmed presence creates exactly one crop. |
| Detection stream counting | 2026-06-29 | `annotated_mjpeg(counter=...)` callback path | Auto stream count/crop no longer depends on `track_id` or ByteTrack. |
| Legacy tracking crop | 2026-06-29 | `CropSession.add_tracked()` retained but unwired from Auto | Reserved for a future conveyor Auto variant. |
| Verification | 2026-06-29 | Backend full suite, frontend full suite, and production build | Backend: 80 passed. Frontend: 27 passed. Build succeeded. |

### Notes

- `count_mode` is now vestigial for Auto `detect-stream`; it remains in the data model for future conveyor behavior.
- GPU + camera manual smoke is deferred to the server: one part, re-entry, brief flash, hand-only/tiny movement, and several sequential parts remain pending.

## [Unreleased] - 2026-06-29 - Live Monitor Auto/Manual Flow

### Summary

Redesigned Live Monitor around an explicit Start Camera -> Auto or Manual -> Review & Send flow. This separates raw preview from AI detection, accumulates crops across a run, lets operators approve only selected crops, and fixes the bug where Stop Detection hid the Send to QC path.

### Added

- `qc_server/app/services/streaming.py` - `grab_one()` helper for one-shot frame capture.
- `qc_server/app/services/crop_session.py` - `CropSession.add_captured()` and `CropSession.approve()` for manual capture and approved crop folders.
- `POST /api/cameras/{camera_id}/crop-session/start` - resets the crop session when the operator starts the camera.
- `POST /api/cameras/{camera_id}/capture` - runs one-shot inference and appends manual crops.
- `POST /api/cameras/{camera_id}/crop-session/approve` - copies selected crops into the approved batch folder.
- `qc_frontend/src/api/cameras.js` - `startCropSession()`, `captureDetection()`, and `approveCrops()` helpers.
- `qc_frontend/src/views/LiveMonitor.vue` - Auto/Manual mode selector, Start Camera, Manual Capture, raw preview, and checkbox crop approval grid.

### Changed

- `qc_server/app/routers/cameras.py` detect stream now attaches to the existing crop session instead of resetting it.
- `qc_frontend/src/views/LiveMonitor.vue` now keeps Review & Send available after Stop Detection.
- Send to QC now submits the approved crop folder returned by `/crop-session/approve`, not the raw session folder.
- `qc_frontend/src/views/__tests__/LiveMonitor.crop.test.js` now covers manual capture, default crop selection, deselect-all disable, and approved-submit behavior.

### Removed

- `CropSession.add_clean_frame()` and the single-snapshot finalize side effect.
- The hidden single-camera snapshot path as an operator-facing flow; Manual Capture is now explicit per run.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Live Monitor flow | 2026-06-29 | Start Camera split from Start Detection, with Auto and Manual run modes | Operators can preview raw camera, run Auto tracking, or capture manually before review. |
| Crop session lifecycle | 2026-06-29 | Explicit start, manual capture append, finalize preview, approve selected files | Start Camera resets; Auto/Manual append; Send uses only approved crops. |
| Backend crop APIs | 2026-06-29 | `/crop-session/start`, `/capture`, `/crop-session/approve`, and `grab_one()` | Manual capture and selected-crop approval are API-backed. |
| Verification | 2026-06-29 | Backend full suite, frontend full suite, and production build | Backend: 73 passed. Frontend: 27 passed. Build succeeded. |

### Notes

- GPU + camera manual smoke is deferred to the server: Auto, Manual, mode-lock, and no-detection capture checks remain pending.

## [Unreleased] - 2026-06-29 - Live Streaming Slice 3 (Count-Gate -> Crop -> QC)

### Summary

Implemented the count approval gate from Live Monitor to QC Studio. The server now captures clean object crops during annotated detection, finalizes them through a crop-session endpoint, and the frontend shows a crop review grid before submitting the existing batch pipeline.

### Added

- `qc_server/app/services/crop.py` - reusable `crop_objects()` helper for clamped bbox crops.
- `qc_server/app/services/crop_session.py` - per-camera `CropSession` registry for single-frame and tracking crop modes.
- `POST /api/cameras/{camera_id}/crop-session/finalize` - finalizes captured crops and returns the server folder plus crop URLs.
- `GET /api/cameras/{camera_id}/crops/{session_ts}/{filename}` - serves saved crop JPEG thumbnails.
- `qc_frontend/src/api/cameras.js` - `finalizeCropSession()` API helper.
- `qc_frontend/src/views/__tests__/LiveMonitor.crop.test.js` - crop gate component coverage using Vue Test Utils and jsdom.

### Changed

- `qc_server/app/services/annotated_stream.py` now accepts a `crop_sink` hook and passes clean original-resolution frames before annotation.
- `qc_server/app/routers/cameras.py` resets a crop session on detection start and writes crops according to camera `count_mode`.
- `qc_frontend/src/views/LiveMonitor.vue` replaces manual source-folder entry with a finalized crop thumbnail grid and disables Confirm when no crops were captured.
- `qc_frontend/package.json` adds Vue component test dependencies for the new Live Monitor test.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Count-gate crop flow | 2026-06-29 | Per-camera crop sessions, finalize endpoint, crop serving, and Live Monitor crop review grid | Operators approve captured object crops before sending a batch to QC. |
| Single camera mode | 2026-06-29 | Latest clean frame + detections are stored and cropped on finalize | Station cameras create snapshot crops when the operator opens Send to QC. |
| Tracking camera mode | 2026-06-29 | Unique `track_id` detections are cropped once during streaming | Conveyor cameras accumulate one crop per tracked object until Stop/Send. |
| Verification | 2026-06-29 | Backend full suite, frontend full suite, and production build | Backend: 64 passed. Frontend: 25 passed. Build succeeded. |

### Notes

- GPU + camera manual smoke is deferred to the server: tracking camera, single camera, and zero-detection gate checks remain pending.
- Deviation: Vue component test dependencies (`@vue/test-utils`, `jsdom`) were added because the repo had only API/utils tests and no existing component test harness.

## [Unreleased] - 2026-06-29 - Detection Confidence Fix

### Summary

Fixed the server object detection path returning zero boxes for low-confidence PCB detections even when the YOLO CLI found valid boxes.

### Fixed

- `qc_server/app/services/object_detection.py` now passes `conf_threshold` into `YOLO(...)` so Ultralytics does not apply its default confidence filter before app filtering.
- `detect()` now reads `results.boxes` directly (`xyxy`, `cls`, `conf`, `names`) instead of depending on the `supervision` adapter for Ultralytics result parsing.

### Added

- `qc_server/tests/test_object_detection.py` verifies `detect()` passes the configured confidence threshold and preserves the existing `Detection` dataclass output shape.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Object detection parsing | 2026-06-29 | Direct Ultralytics box parsing with configured confidence passed into inference | `detect()` returns the same low-confidence PCB boxes as the YOLO CLI path. |
| Detection Test verification | 2026-06-29 | GPU inference and browser upload smoke on `temp/test-pcb.png` with `pcb-1.pt` at `conf=0.1` | Service/API/page path returns and renders 3 PCB detections. |
| Verification | 2026-06-29 | Backend pytest, frontend build/test, real model inference, and Playwright upload smoke | Backend: 52 passed. Frontend: build passed, 23 tests passed. Detection Test page rendered 3 boxes. |

### Notes

- Root cause: `detect()` called `model(frame, verbose=False)`, so Ultralytics filtered with its default confidence before the app's lower threshold was applied.
- Checked first hypothesis: `supervision.Detections.from_ultralytics(...)` parsed 3 detections on this server, so the adapter was not the immediate zero-box cause.

## [Unreleased] - 2026-06-29 - Detection Test Slice 2.4

### Summary

Added a server-gated Detection Test workflow for validating the active YOLO model on uploaded sample images or videos before using it in live production streams.

### Added

- `qc_server/requirements.txt` - `python-multipart` for upload endpoints.
- `qc_server/app/database.py` - generic guarded `ensure_column()` migration helper.
- `qc_server/app/models.py` / `qc_server/app/schemas.py` - `Setting.input_mode_enabled`.
- `qc_server/app/routers/detect.py` - `POST /api/detect/image`, `POST /api/detect/video`, and `GET /api/detect/video/{video_id}/stream`.
- `qc_frontend/src/api/detect.js` - upload API helpers for image/video detection tests.
- `qc_frontend/src/views/DetectionTest.vue` - image/video upload page with annotated image results, detection list, and annotated MJPEG video playback.
- Backend tests for the guarded `input_mode_enabled` migration/settings API and detect router.

### Changed

- Settings now includes an `input_mode_enabled` toggle for showing/hiding the Detection Test navigation item.
- Sidebar conditionally shows the Detection Test route from the server-backed setting.
- README and AGENTS now document Slice 2.4, `/api/detect/*`, and the new page.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Detection test backend | 2026-06-29 | Upload endpoints for images/videos, annotated result encoding, and MJPEG video playback | Operators can test the active model with sample files through `qc_server`. |
| Settings gate | 2026-06-29 | Guarded `input_mode_enabled` column plus API schema/update support | Existing SQLite DBs are preserved; production can hide the test page from nav. |
| Detection Test UI | 2026-06-29 | `/detect-test` route, upload mode toggle, result preview/list | Dashboard can validate active model behavior outside live RTSP feeds. |
| Verification | 2026-06-29 | Backend and frontend suites run locally | Backend: 51 passed. Frontend: build passed, 23 tests passed. GPU model smoke pending on server. |

### Notes

- Branch: `feat/detection-test-page` (unmerged; pushed for plan-author review).
- Open: Task 4 Step 5 GPU model smoke must run on the server with a real model/image/video.

## [Unreleased] - 2026-06-29 - Live Streaming Slice 2.3

### Summary

Polished detection operator UX and reduced live stream lag. Settings now uses decimal confidence, a single Active Model selector, and a save toast; the annotated MJPEG stream is downscaled/FPS-capped and `/count` reports live FPS for the metric strip.

### Added

- `qc_server/app/config.py` - `stream_max_width` and `stream_max_fps` settings.
- `qc_server/app/services/annotated_stream.py` - `downscale(frame, max_width)` helper plus FPS tracking/capping in `annotated_mjpeg()`.
- `qc_frontend/src/composables/useToast.js` - singleton app toast composable.
- App-level toast rendering in `qc_frontend/src/App.vue`.
- `/api/cameras/{camera_id}/count` now returns `{"count": int, "fps": float}`.

### Changed

- Annotated MJPEG detection now downscales frames before `detect()` so boxes stay aligned with the encoded frame.
- Live Monitor now reads real FPS from `/count` instead of the camera mock value.
- Settings model config now shows confidence as a decimal number input and saves only confidence, defect strategy, and active model.
- README and AGENTS now document Slice 2.3 stream performance and Settings UX.

### Removed

- Settings free-text Detection Model and Segmentation Model fields.
- Settings confidence percentage slider.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Detection stream performance | 2026-06-29 | `stream_max_width`, `stream_max_fps`, downscale-before-detect, FPS cap | Annotated MJPEG sends smaller frames and avoids unbounded loop rate. |
| Live metrics | 2026-06-29 | `/count` returns count and FPS; Live Monitor consumes both | Metric strip shows live stream FPS from the backend. |
| Settings UX | 2026-06-29 | Decimal confidence input, single Active Model selector, save toast | Model config is less ambiguous and confirms saves. |
| Verification | 2026-06-29 | Backend and frontend suites run locally | Backend: 46 passed. Frontend: build passed, 23 tests passed. GPU/RTSP smoothness + FPS smoke pending on server. |

### Notes

- Branch: `feat/live-streaming-slice2` (unmerged; pushed for plan-author review).
- Open: Task 3 Step 3 GPU/RTSP smoothness + FPS smoke must run on the server.

## [Unreleased] - 2026-06-29 - Live Streaming Slice 2.2

### Summary

Reworked live detection transport from the fragile WebSocket/base64 path to server-annotated MJPEG with a threaded latest-frame grabber. The UI now renders the annotated stream as an `<img>` and polls a tiny `/count` endpoint for the metric strip.

### Added

- `qc_server/app/services/frame_grabber.py` - threaded latest-frame camera reader that drops stale frames.
- `qc_server/app/services/annotated_stream.py` - server-side detection annotation, JPEG encoding, and multipart MJPEG generator.
- `qc_server/app/services/detect_tracker.py` - lazy `supervision` tracker helper extracted for the smoke-only tracking path.
- `GET /api/cameras/{camera_id}/detect-stream` - annotated MJPEG detection/counting endpoint.
- `GET /api/cameras/{camera_id}/count` - latest live count JSON endpoint for the dashboard.
- Backend tests for the frame grabber, annotated MJPEG service, and detect-stream/count routes.

### Changed

- `qc_frontend/src/views/LiveMonitor.vue` now renders the annotated detection feed with `<img>` and polls `/count` every second while detection is running.
- `qc_frontend/vite.config.js` removed the `/api` WebSocket proxy flag because detection transport is HTTP-only.
- `README.md` and `AGENTS.md` now document annotated MJPEG detection transport and `/count`.

### Fixed

- Removed the WebSocket keepalive race path that could trigger `websockets` `AssertionError`.
- Latest-frame grabbing drops stale RTSP frames instead of building lag toward 0 FPS.

### Removed

- `WEBSOCKET /api/cameras/{camera_id}/detect`.
- `qc_server/app/services/detect_stream.py`.
- `qc_server/tests/test_detect_ws.py`.
- Frontend canvas/base64/WebSocket detection rendering.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Detection transport | 2026-06-29 | Annotated MJPEG `/detect-stream` + `<img>` frontend | No WebSocket/base64 transport remains in the live detection path. |
| Camera frame capture | 2026-06-29 | `FrameGrabber` thread keeps only latest frame | RTSP lag is reduced by dropping stale frames. |
| Live count | 2026-06-29 | `/count` endpoint + 1s frontend poll | Metric strip updates independently from MJPEG image transport. |
| Tracking path | 2026-06-29 | Lazy `detect_tracker.apply_tracker()` helper | `supervision` stays server-only and smoke-verified. |
| Verification | 2026-06-29 | Backend and frontend suites run locally | Backend: 44 passed. Frontend: build passed, 23 tests passed. GPU/RTSP smoke pending on server. |

### Notes

- Branch: `feat/live-streaming-slice2` (unmerged; pushed for plan-author review).
- Open: Task 4 Step 5 GPU/RTSP smoke must run on the server before merge.

## [Unreleased] - 2026-06-29 - Live Streaming Slice 2.1

### Summary

Replaced the one-path detection model config with a models folder plus Settings switcher. The backend now lists `.pt` files from `qc_server/models/`, persists `settings.active_model`, and resolves the selected file for live detection.

### Added

- `qc_server/app/database.py` - guarded `ensure_active_model_column()` SQLite migration for existing server databases.
- `qc_server/app/models.py` / `qc_server/app/schemas.py` - `Setting.active_model` persistence and API schema support.
- `GET /api/models` - lists sorted `.pt` files from `settings.models_dir` and returns the active model.
- `qc_frontend/src/api/models.js` - model list API wrapper.
- Settings UI active-model dropdown populated from `/api/models`.
- Backend tests for the guarded migration, `/api/models`, `active_model` persistence, and no-active-model WebSocket close path.

### Changed

- `qc_server/app/services/object_detection.py` now resolves the selected model from `active_model + models_dir` and reloads YOLO when the path changes.
- `qc_server/app/routers/cameras.py` no longer gates detection on `MQC_MODEL_PATH`; it closes `1011 "model not configured"` when no selected `.pt` exists.
- `qc_frontend/src/api/settings.js` and `useSettings.js` now map `active_model` / `activeModel`.
- `README.md` and `AGENTS.md` now document the model folder workflow and active model switcher.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Model storage | 2026-06-29 | `models_dir` config and `.pt` folder listing | Drop weights into `qc_server/models/`; weights stay gitignored. |
| Settings persistence | 2026-06-29 | Guarded `active_model` column migration | Existing SQLite data is preserved; selection persists through `PUT /api/settings`. |
| Live detection | 2026-06-29 | `resolve_model_path(setting)` + model cache keyed by path | Detection uses the active model and reloads when selection changes. |
| Settings UI | 2026-06-29 | Active Model dropdown | Operators select the live detection model without editing env vars. |
| Verification | 2026-06-29 | Backend and frontend suites run locally | Backend: 40 passed. Frontend: build passed, 23 tests passed. GPU model smoke pending on server. |

### Notes

- Branch: `feat/live-streaming-slice2` (unmerged; pushed for plan-author review).
- Deviations: plan referenced `object_detection.py`; that file already exists in the branch and was updated directly.
- Open: Task 4 Step 7 GPU smoke must run on the server with real camera/model before merge.

## [Unreleased] - 2026-06-29 - Live Streaming Slice 2

### Summary

Added detection/counting overlay for Live Monitor through a backend WebSocket. The backend streams JPEG frames plus serialized detections/counts from a server-only YOLO path, while the frontend renders frames and boxes on a canvas.

### Added

- `qc_server/requirements-ml.txt` - server-only `ultralytics` and `supervision` dependency pins; CUDA-matched `torch` remains a server install prerequisite.
- `qc_server/app/services/inference/__init__.py` - object `Detection` dataclass, pure `serialize_detections`, lazy `load_model()`, and lazy `detect()` using `MQC_MODEL_PATH`.
- `qc_server/app/services/counting.py` - pure `count_single` and `update_tracking` helpers.
- `qc_server/app/services/detect_stream.py` - detection message generator that reads camera frames, runs detection, applies optional ByteTrack tracking, and yields base64 frame/detection/count JSON.
- `WEBSOCKET /api/cameras/{camera_id}/detect` - forwards detection messages and closes with `1011` when the camera or model config is unavailable.
- Backend tests for detection serialization, counting helpers, and the WebSocket route. Backend suite: 36 tests green.

### Changed

- `qc_frontend/src/views/LiveMonitor.vue` now opens the detection WebSocket on Start, draws incoming frames on a canvas, overlays detection boxes/labels, updates live object count, and closes the socket on Stop/unmount.
- `qc_frontend/vite.config.js` enables `ws: true` for the `/api` dev proxy.
- `id.js` and `en.js` add `live.modelNotConfigured` for the unset `MQC_MODEL_PATH` close path.
- `README.md` and `AGENTS.md` now document Live Streaming Slice 2, server-only ML dependencies, and the retained MJPEG fallback.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Detection transport | 2026-06-29 | WebSocket `/api/cameras/{id}/detect` yielding `frame`, `detections`, and `count` | Browser receives live inference payloads without removing raw MJPEG fallback. |
| Object inference | 2026-06-29 | Lazy YOLO load from `MQC_MODEL_PATH`; ML imports stay inside functions | Laptop tests pass without ML deps, GPU server owns real model smoke. |
| Counting | 2026-06-29 | Pure single-frame and cumulative tracking count helpers | `single` returns per-frame detection count; `tracking` counts unique track IDs. |
| Live Monitor | 2026-06-29 | Canvas frame render + vector boxes + live count | Start/Stop controls own the WebSocket lifecycle; unset model path shows a config error. |
| Verification | 2026-06-29 | Backend and frontend suites run locally | Backend: 36 passed. Frontend: build passed, 23 tests passed. GPU model smoke pending on server. |

### Notes

- Branch: `feat/live-streaming-slice2` (unmerged; pushed for plan-author review).
- Deviations: existing `app/services/inference/` package already existed for defect strategies, so object detection exports were added to its `__init__.py` instead of creating a conflicting `inference.py` file.
- Open: Task 4 Step 6 GPU smoke must run on the server with real camera/model before merge.

## [Unreleased] - 2026-06-28 - Live Streaming Slice 1

### Summary

Added server-side RTSP/USB camera streaming through OpenCV-backed MJPEG and real camera reachability status. Live Monitor now renders the real stream through `/api/cameras/{id}/stream`, refreshes camera status every 10 seconds, and removes fake bounding boxes/counting until Slice 2.

### Added

- `qc_server/app/services/streaming.py` - OpenCV capture seam, source probe, and MJPEG multipart frame generator.
- `qc_server/app/services/camera_monitor.py` - background poll loop that updates each camera status to `online` or `offline`.
- `GET /api/cameras/{camera_id}/stream` - uniform MJPEG stream endpoint for registered cameras.
- `opencv-python-headless==4.*` backend dependency.
- Backend tests for streaming service, stream endpoint, and camera status monitor. Backend suite: 30 tests green.
- i18n keys `live.offlineNoSignal` and `live.detectionSlice2` in `id.js` and `en.js`.

### Changed

- `LiveMonitor.vue` now uses the MJPEG endpoint as an `<img>` feed when the selected camera is online.
- `LiveMonitor.vue` now refreshes camera status periodically and shows an offline placeholder for offline cameras.
- `LiveMonitor.vue` removed the fake object counter timer and bounding-box overlay; Send to QC remains available while streaming because the Source Folder is entered manually.
- `README.md` and `AGENTS.md` now document Live Streaming Slice 1 and the OpenCV backend dependency.

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Camera streaming | 2026-06-28 | OpenCV `VideoCapture` + MJPEG multipart generator | Browser consumes `/api/cameras/{id}/stream` uniformly for RTSP/USB/server-reachable sources. |
| Camera status | 2026-06-28 | Background monitor probes each camera source every 20 seconds | Camera `status` reflects reachability; tests disable the monitor via `MQC_CAMERA_MONITOR_ENABLED=false`. |
| Live Monitor | 2026-06-28 | Real stream image, periodic camera refresh, offline placeholder | Fake bounding boxes/counting removed; detection/counting deferred to Slice 2. |
| Verification | 2026-06-28 | Backend + frontend suites run locally | Backend: 30 passed. Frontend: build passed, 23 tests passed. Linux real-camera smoke still requires server access. |

### Notes

- Branch: `feat/live-streaming-slice1` (unmerged; pushed for plan-author review).
- Deviations: `superpowers:executing-plans` was requested but not available in this Codex environment; executed directly from the saved plan. Real RTSP Linux smoke was not run on this Windows workspace.

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
