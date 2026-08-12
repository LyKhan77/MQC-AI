# Inspect Measurement Prototype — Milestone Tracker

**Feature PRD:** [`inspect-measurement-prototype.md`](./inspect-measurement-prototype.md)
**Status terakhir:** M0–M5, M7, I1–I3 software implemented; M6/I4 physical accuracy pending
**Last updated:** 12 August 2026

Dokumen ini adalah checkpoint implementasi. Update setelah setiap milestone selesai. Status `DONE` membutuhkan evidence berupa file/commit dan test atau browser verification yang relevan.

## Status legend

- `DONE` — selesai dan sudah diverifikasi.
- `IN PROGRESS` — sedang dikerjakan; belum boleh dianggap usable.
- `PLANNED` — sudah didefinisikan, belum dikerjakan.
- `BLOCKED` — ada dependency eksternal atau keputusan yang belum tersedia.
- `DEFERRED` — sengaja dipindahkan ke versi proper.

## Current checkpoint

| Checkpoint | Status | Evidence | Catatan |
|---|---|---|---|
| Feature PRD | `DONE` | `docs/PRD/Features/inspect-measurement-prototype.md` | Scope, constraints, acceptance criteria, dan risk sudah ditulis. |
| 2D geometry improvement design | `DONE` | `docs/PRD/Features/inspect-measurement-2d-geometry-improvement-design.md` | Logical edge, dual-axis calibration, corner radius, bend angle, UX, compatibility, dan verification disetujui. |
| Implementation plan | `DONE` | `docs/superpowers/plans/2026-08-07-inspect-measurement-prototype.md` | Task backend, frontend, test, dan verification sudah dipecah. |
| Standalone HTML demo | `DONE` | `temp/measurement-studio-demo.html` | Demo visual saja; bukan production measurement engine. |
| Prototype Live Camera contract | `DONE` | Prototype PRD + implementation plan | Preview + one-shot trigger capture ditambahkan; continuous measurement tetap di luar scope. |
| Production measurement backend | `DONE` | `qc_server/app/services/measurement.py`, `qc_server/app/routers/measurements.py` | OpenCV process, dual-axis calibration, logical-edge fit/dedup, corner arc, bend candidate, upload/Live Camera/Mobile Camera metadata, persistence, evaluate, dan audit tersedia. |
| Production Measurement Studio route | `DONE` | `qc_frontend/src/views/MeasurementStudio.vue` | `/measurement` mendukung multi-task dimension/corner/bend, Image/Live/Mobile capture, X/Y calibration, candidate selection, tolerance, evaluate, dan guidance pose. |
| History + Audit integration | `DONE` | MeasurementRun API + component tests | Save, History search/reopen/delete, dan audit actions tersedia. |
| Accuracy validation | `PLANNED` | — | Belum ada physical reference sample/evidence. |

**Current implementation boundary:** prototype production flow M0–M5 dan M7 selesai. Improvement I1–I3 software slice selesai. M6/I4 tetap menunggu reference artifact, repeatability, dan physical station evidence; belum ada klaim akurasi produksi.

## Milestone checklist

| ID | Milestone | Documentation | Implementation | Exit checkpoint |
|---|---|---|---|---|
| M0 | Contract & calibration | `DONE` | `DONE` | Data shape, status rules, manual scale, dan synthetic fixtures disetujui serta diuji. |
| M1 | OpenCV measurement kernel | `DONE` | `DONE` | Service mengembalikan candidate edge, px-to-mm, geometry, confidence, dan `REVIEW` gate. |
| M2 | Backend vertical slice | `DONE` | `DONE` | Process → save → list/detail → delete berjalan melalui API dan TestClient. |
| M3 | Measurement Studio input/process | `DONE` | `DONE` | Inspector upload, trigger Live Camera, atau capture Mobile Camera; calibration overlay, process, dan candidate overlay tersedia. |
| M4 | Tolerance & evaluate | `DONE` | `DONE` | Tolerance per item mengubah min/max/deviation/status dan summary. |
| M5 | History & audit UX | `DONE` | `DONE` | Saved run dapat dicari, dibuka kembali, dihapus dengan confirmation, dan tercatat di audit. |
| M6 | Accuracy gate | `DONE` | `PLANNED` | Reference sample, repeatability, failure cases, dan error report tersedia. |

## Checkpoint detail

### M0 — Contract & calibration

- [x] Pydantic contract measurement item disetujui.
- [x] `PASS`, `FAIL`, `REVIEW` rules disetujui.
- [x] Reference line calibration menghasilkan `mm_per_pixel`.
- [x] Invalid/zero/negative calibration ditolak.
- [x] Synthetic geometry fixture tersedia.

### M1 — OpenCV measurement kernel

- [x] LSD menjadi detector utama.
- [x] `HoughLinesP` menjadi fallback.
- [x] Preprocessing dan filtering noise berjalan.
- [x] Candidate edge memiliki endpoint, pixel length, angle, confidence, dan source method.
- [x] Geometry linear/angle/hole memiliki unit test.

### M2 — Backend vertical slice

- [x] `POST /api/measurements/process` berjalan.
- [x] `POST /api/measurements` menyimpan run.
- [x] `GET /api/measurements` dan detail berjalan.
- [x] Delete membersihkan metadata dan file milik run.
- [x] Path containment dan invalid image memiliki guard di router.
- [x] Audit event backend tercatat.

### M3 — Measurement Studio input/process

- [x] Route `/measurement` tersedia.
- [x] Upload/dropzone dan manual run name berjalan.
- [x] Live Camera selector, preview, dan one-shot trigger capture berjalan.
- [x] Mobile Camera tab, HTTPS permission flow, preview, dan one-shot capture berjalan.
- [x] Calibration overlay berjalan.
- [x] Candidate line dan selected geometry terlihat di canvas.
- [x] Processing/error state jelas bagi inspector.

### M4 — Tolerance & evaluate

- [x] Default linear `±2.0 mm`.
- [x] Default angle `±0.5°`.
- [x] Tolerance dapat dioverride per item.
- [x] Nominal wajib sebelum evaluate.
- [x] `REVIEW` mengalahkan `PASS` dan `FAIL` jika calibration/edge tidak valid.
- [x] Backend menghitung ulang hasil sebelum save.

### M5 — History & audit UX

- [x] Saved run muncul newest first.
- [x] Search/filter nama dan source berjalan.
- [x] Reopen mempertahankan image, calibration, geometry, tolerance, dan verdict.
- [x] Delete memakai confirmation.
- [x] UI actions tidak membuat audit duplicate dengan server events.

### M6 — Accuracy gate

- [ ] Known-scale planar sample diuji.
- [ ] Rotated sample diuji.
- [ ] Glare/noise sample diuji.
- [ ] Invalid-calibration sample menghasilkan `REVIEW`.
- [ ] Absolute error dan repeatability dicatat.
- [ ] Tidak ada klaim produksi ±2 mm atau ±0.5° tanpa evidence station.

## M7 - Multi-view session and scale profile slice

**Status:** `DONE` (software); physical accuracy remains pending.

- [x] Manual component/series naming.
- [x] Multiple Image inputs staged as separate views.
- [x] Live Camera trigger and Mobile Camera capture append views without implicit processing.
- [x] Selected-view calibration -> explicit Process Measurement -> evaluate flow.
- [x] `TOP_FACE`, `REVERSE_FACE`, `PROFILE_FACE`, `CUSTOM_FACE` guidance and thickness/bend pose gate.
- [x] Global/Detail profile CRUD, camera/resolution validation, capability warning.
- [x] Save/reopen/delete views, session completion guard, History, and Audit persistence.
- [ ] Physical station calibration, repeatability, and production accuracy gate.

Evidence: commits `edb2cfd`, `573a745`, `784f218`, `c728f0b`, `995017f`, `663f018`; focused backend/frontend tests, build, and Measurement Studio Playwright coverage.

## Accuracy improvement checkpoints

| ID | Checkpoint | Documentation | Implementation | Exit checkpoint |
|---|---|---|---|---|
| I1 | Approved 2D geometry design | `DONE` | — | Scope, algorithms, API migration, UX, and verification contract approved. |
| I2 | Logical edge + calibration v2 | `DONE` | `DONE` | Dual-axis calibration, merged/fitted/deduplicated logical edges, outer-span measurement, calibration quality gate, and overlay layers pass focused tests. |
| I3 | Corner + bend geometry | `DONE` | `DONE` | Multi-select task flow, selected outer-radius fit, bend candidate filtering, selected flange-pair angle, and `REVIEW` reasons pass focused tests. |
| I4 | Physical accuracy gate | `DONE` | `PLANNED` | Stage 1 station, traceable artifact, repeated captures, error report, and drift limits available. |

Implementation source: [`inspect-measurement-2d-geometry-improvement-design.md`](./inspect-measurement-2d-geometry-improvement-design.md).

### I2 — Logical edge + calibration v2

- [x] Independent X/Y reference lines validate orientation and scale.
- [x] Legacy one-line calibration remains readable for saved history.
- [x] LSD `LSD_REFINE_ADV` metadata and Hough fallback remain available.
- [x] Fragmented collinear candidates merge into fitted logical edges.
- [x] Thick-stroke duplicates collapse to one logical edge per boundary.
- [x] Outer-span measurement uses anisotropic X/Y scale.
- [x] Calibration quality and non-independent demo calibration gate verdicts to `REVIEW`.

Evidence: commit `5c607c0`; backend focused measurement suite `62 passed`; full backend suite `244 passed`.

### I3 — Corner + bend geometry

- [x] `corner_radius` fits circular arcs from contour turning-point clusters.
- [x] Corner candidates expose radius, coverage, residual, confidence, and review reason.
- [x] `bend_angle` derives angle from two finite logical flange edges.
- [x] Bend intersections outside edge endpoints are rejected.
- [x] Dimension, corner, and bend checks can be selected in one process.
- [x] Studio shows task-specific candidate cards and simple selection guidance.
- [x] Bend tolerance defaults to `±0.5°`; weak geometry stays `REVIEW`.

Evidence: commit `b314fb6`; frontend `198 passed`, production build passed, Measurement Studio E2E `10 passed`.

## Update protocol

Setelah milestone berubah:

1. Update kolom `Implementation`.
2. Centang hanya item yang benar-benar diverifikasi.
3. Tambahkan commit, test command, atau screenshot/browser evidence.
4. Catat known gap jika milestone belum sepenuhnya memenuhi target.
5. Update `Last updated`.

## Progress log

| Date | Checkpoint | Evidence | Result |
|---|---|---|---|
| 2026-08-07 | PRD + plan | Commit `0b87f49` | Documentation complete; production implementation not started. |
| 2026-08-10 | M0–M5 prototype implementation | Feature branch verification: backend `202 passed`, frontend `157 passed`, build passed, Playwright `5 passed`; sample kernel smoke `42 candidates` | Production prototype flow complete; M6 physical accuracy validation pending. |
| 2026-08-12 | I1 2D geometry improvement design | Approved design spec + PRD/milestone synchronization | Implementation planning may start; no geometry code changed yet. |
| 2026-08-10 | Measurement Studio UI + Mobile Camera | Backend `204 passed`, frontend `160 passed`, build passed, Playwright `7 passed`; scoped overflow assertion | QC Studio-style fixed shell; History and Measurement Items scroll independently; Mobile Camera uses browser `getUserMedia()` and same process pipeline. |
| 2026-08-10 | Measurement canvas alignment + controls | Frontend `162 passed`, build passed, Playwright `8 passed`; image/SVG bounding-box assertion | Wider QC Studio-style panels; shared image frame fixes overlay alignment; zoom/pan and high-contrast candidate overlays implemented. |
| 2026-08-10 | Measurement rail overflow + overlay weight | Targeted component `10 passed`, Measurement E2E `5 passed` | Fixed flex rails now mirror QC Studio positioning; Input/Calibration rail scrolls independently; LSD foreground stroke reduced to 3px. |
| 2026-08-10 | Measurement shell redesign | Frontend `162 passed`, build passed, Playwright `9 passed`; TopBar/full-height shell assertion | Title moved to application TopBar; outer padding/border removed; desktop workspace now matches QC Studio's fixed `280px / flex / 320px` layout; source/process/status controls float over the canvas. |
| 2026-08-12 | I2 logical edge + calibration v2 | Commit `5c607c0`; backend focused `62 passed`; full backend `244 passed` | Dual-axis calibration, logical-edge merge/fit/dedup, outer-span geometry, calibration quality gate, and object-detection cache regression fix implemented. |
| 2026-08-12 | I3 corner + bend geometry | Commit `b314fb6`; frontend `198 passed`; build passed; Measurement Studio E2E `10 passed` | Rounded-corner radius, bend-angle candidates, multi-task selection, selection guidance, tolerance defaults, and geometry overlays implemented. Physical accuracy remains pending. |
