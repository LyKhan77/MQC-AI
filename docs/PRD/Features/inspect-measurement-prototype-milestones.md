# Inspect Measurement Prototype — Milestone Tracker

**Feature PRD:** [`inspect-measurement-prototype.md`](./inspect-measurement-prototype.md)
**Status terakhir:** M0–M5 implemented; M6 accuracy validation pending
**Last updated:** 10 August 2026

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
| Implementation plan | `DONE` | `docs/superpowers/plans/2026-08-07-inspect-measurement-prototype.md` | Task backend, frontend, test, dan verification sudah dipecah. |
| Standalone HTML demo | `DONE` | `temp/measurement-studio-demo.html` | Demo visual saja; bukan production measurement engine. |
| Prototype Live Camera contract | `DONE` | Prototype PRD + implementation plan | Preview + one-shot trigger capture ditambahkan; continuous measurement tetap di luar scope. |
| Production measurement backend | `DONE` | `qc_server/app/services/measurement.py`, `qc_server/app/routers/measurements.py` | OpenCV process, upload/Live Camera/Mobile Camera source metadata, persistence, file serving, server-side evaluate, dan audit tersedia. |
| Production Measurement Studio route | `DONE` | `qc_frontend/src/views/MeasurementStudio.vue` | `/measurement` mendukung upload, Live Camera trigger, Mobile Camera capture, calibration overlay, candidate selection, tolerance, dan evaluate. |
| History + Audit integration | `DONE` | MeasurementRun API + component tests | Save, History search/reopen/delete, dan audit actions tersedia. |
| Accuracy validation | `PLANNED` | — | Belum ada physical reference sample/evidence. |

**Current implementation boundary:** prototype production flow M0–M5 selesai dan terverifikasi. M6 masih menunggu reference artifact, repeatability, dan physical station evidence.

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
| 2026-08-10 | Measurement Studio UI + Mobile Camera | Backend `204 passed`, frontend `160 passed`, build passed, Playwright `7 passed`; scoped overflow assertion | QC Studio-style fixed shell; History and Measurement Items scroll independently; Mobile Camera uses browser `getUserMedia()` and same process pipeline. |
