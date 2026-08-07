# Inspect Measurement Prototype — Milestone Tracker

**Feature PRD:** [`inspect-measurement-prototype.md`](./inspect-measurement-prototype.md)
**Status terakhir:** Documentation complete; implementation not started
**Last updated:** 7 August 2026

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
| Production measurement backend | `PLANNED` | — | Belum ada service/API measurement. |
| Production Measurement Studio route | `PLANNED` | — | Belum ada route `/measurement`. |
| History + Audit integration | `PLANNED` | — | Belum ada `MeasurementRun` persistence. |
| Accuracy validation | `PLANNED` | — | Belum ada physical reference sample/evidence. |

**Current implementation boundary:** belum ada milestone production code yang berstatus `DONE`. Yang selesai baru dokumentasi dan visual demo.

## Milestone checklist

| ID | Milestone | Documentation | Implementation | Exit checkpoint |
|---|---|---|---|---|
| M0 | Contract & calibration | `DONE` | `PLANNED` | Data shape, status rules, manual scale, dan synthetic fixtures disetujui serta diuji. |
| M1 | OpenCV measurement kernel | `DONE` | `PLANNED` | Service mengembalikan candidate edge, px-to-mm, geometry, confidence, dan `REVIEW` gate. |
| M2 | Backend vertical slice | `DONE` | `PLANNED` | Process → save → list/detail → delete berjalan melalui API dan TestClient. |
| M3 | Measurement Studio input/process | `DONE` | `PLANNED` | Inspector upload atau trigger Live Camera, calibration, process, dan melihat overlay candidate. |
| M4 | Tolerance & evaluate | `DONE` | `PLANNED` | Tolerance per item mengubah min/max/deviation/status dan summary. |
| M5 | History & audit UX | `DONE` | `PLANNED` | Saved run dapat dicari, dibuka kembali, dihapus dengan confirmation, dan tercatat di audit. |
| M6 | Accuracy gate | `DONE` | `PLANNED` | Reference sample, repeatability, failure cases, dan error report tersedia. |

## Checkpoint detail

### M0 — Contract & calibration

- [ ] Pydantic contract measurement item disetujui.
- [ ] `PASS`, `FAIL`, `REVIEW` rules disetujui.
- [ ] Reference line calibration menghasilkan `mm_per_pixel`.
- [ ] Invalid/zero/negative calibration ditolak.
- [ ] Synthetic geometry fixture tersedia.

### M1 — OpenCV measurement kernel

- [ ] LSD menjadi detector utama.
- [ ] `HoughLinesP` menjadi fallback.
- [ ] Preprocessing dan filtering noise berjalan.
- [ ] Candidate edge memiliki endpoint, pixel length, angle, confidence, dan source method.
- [ ] Geometry linear/angle/hole memiliki unit test.

### M2 — Backend vertical slice

- [ ] `POST /api/measurements/process` berjalan.
- [ ] `POST /api/measurements` menyimpan run.
- [ ] `GET /api/measurements` dan detail berjalan.
- [ ] Delete membersihkan metadata dan file milik run.
- [ ] Path traversal dan invalid image ditolak.
- [ ] Audit event backend tercatat.

### M3 — Measurement Studio input/process

- [ ] Route `/measurement` tersedia.
- [ ] Upload/dropzone dan manual run name berjalan.
- [ ] Live Camera selector, preview, dan one-shot trigger capture berjalan.
- [ ] Calibration overlay berjalan.
- [ ] Candidate line dan selected geometry terlihat di canvas.
- [ ] Processing/error state jelas bagi inspector.

### M4 — Tolerance & evaluate

- [ ] Default linear `±2.0 mm`.
- [ ] Default angle `±0.5°`.
- [ ] Tolerance dapat dioverride per item.
- [ ] Nominal wajib sebelum evaluate.
- [ ] `REVIEW` mengalahkan `PASS` dan `FAIL` jika calibration/edge tidak valid.
- [ ] Backend menghitung ulang hasil sebelum save.

### M5 — History & audit UX

- [ ] Saved run muncul newest first.
- [ ] Search/filter nama dan verdict berjalan.
- [ ] Reopen mempertahankan image, calibration, geometry, tolerance, dan verdict.
- [ ] Delete memakai confirmation.
- [ ] UI actions tidak membuat audit duplicate dengan server events.

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
