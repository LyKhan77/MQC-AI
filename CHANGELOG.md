# CHANGELOG

> **Agent Memory Contract.** This file is the single source of truth for what changed, when, and why. Every AI agent working on this repo MUST read this file before starting work and MUST append an entry after committing changes. See `AGENTS.md` section "Documentation Maintenance" for the full contract.

All notable changes to the MQC-AI project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [Semantic Versioning](https://semver.org/).

Each entry contains:
1. Standard Keep a Changelog categories (Added / Changed / Fixed / Removed)
2. **Current Codebase State** table tracing what was developed and the resulting state

---

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

### Current Codebase State

| Area / Feature | Timeline | What Was Developed | After the Change |
|---|---|---|---|
| Batch deletion API | 2026-06-30 | `DELETE /api/batches/{batch_id}` with image/defect cleanup and result directory removal | Operators can remove obsolete processed batches without deleting source crop folders. |
| Batch History UI | 2026-06-30 | Delete button, confirmation dialog, local row removal, and component test | Batch deletion is explicit and reversible until confirmed. |
| Sidebar branding | 2026-06-30 | Expanded `GSPE | MQC-AI` lockup and collapsed centered `GSPE` | The collapsed sidebar no longer clips or left-aligns the brand mark. |
| Verification | 2026-06-30 | Backend full suite, frontend full suite, and production build | Backend: 82 passed, 2 warnings. Frontend: 28 passed. Build succeeded. |

### Notes

- Deviation: the plan's `t('batches.confirmDelete', )` typo was corrected to `t('batches.confirmDelete')`.
- Deviation: the plan's negative `letter-spacing` on `GSPE` was changed to `0` to follow the higher UI rule that letter spacing must not be negative.
- Browser smoke is pending for reviewer: delete confirm/cancel flow and collapsed sidebar centering.

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
