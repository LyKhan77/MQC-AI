# Inspect Measurement — Geometry Kernel v2 Design

**Status:** Approved for implementation
**Date:** 07 September 2026
**Parent:** [`inspect-measurement-prototype.md`](./inspect-measurement-prototype.md) · [`inspect-measurement-2d-geometry-improvement-design.md`](./inspect-measurement-2d-geometry-improvement-design.md)
**Branch:** `feat/inspect-measurement-geometry-v2` (cut dari `feat/inspect-measurement-prototype` @ `8e08dfa`)

## 1. Tujuan

Memperbaiki akurasi dan stabilitas verdict measurement komponen bending. Evidence test dummypart-012:

- Repeatability antar capture stabil (0.x mm) — pipeline grouping tidak diubah.
- Edge memiliki bias konsisten +0.5 sampai +1.5 mm.
- Corner radius tidak stabil: 5.04 mm normal vs 2.02 mm rotated.
- Drawing memakai definisi **overall outside (bounding box)** untuk ukuran X/Y, sedangkan engine saat ini mengukur span garis lurus (support-bounded) — secara struktural lebih pendek dari drawing ~2×R per sisi berkoma.

Scope: geometry engine saja. Verdict rules (`evaluate_item`), guard band, dan subpixel edge tidak termasuk.

## 2. Diagnosis metode saat ini

| Gejala | Akar penyebab di `measurement.py` |
|---|---|
| Edge bias +0.5–1.5 mm | Endpoint dari min/max proyeksi edge-pixel support (band ±3px) — bocor ke region corner arc dan sensitif pixel liar; tidak ada endpoint geometris |
| Corner 5.04 vs 2.02 rotated | `fit_circle` memakai Kåsa algebraic fit — terkenal bias underestimate radius pada arc pendek (Chernov 2009); window turning-angle dalam jumlah titik kontur, bukan arclength fisik; titik segmen lurus di tepi cluster ikut fit |
| Overall X/Y tidak cocok drawing | Tidak ada task overall/outer envelope; support span satu edge bukan definisi bounding box |
| Bend angle | Tidak perlu diubah — `bend_geometry` sudah memakai arah garis fit (kedua endpoint di garis fit) |

## 3. Perubahan (additive)

### 3.1 Taubin circle fit

`fit_circle` diganti dari Kåsa ke **Taubin fit** (closed form, numpy saja): momen (z0, u, v) di koordinat terpusat, akar kuadrat `det(M − λ·diag(1,1,0))`, null-vector SVD, `a = −B/2A`, `R² = a² + b² + z̄`. Kontrak fungsi tetap `(center, radius, residual)`.

### 3.2 Corner segmentation v2

- Window turning-angle dalam **arclength fisik**: `corner_window_mm` (default 2.0) → `window_px / mean_step`, minimum 4 titik.
- **Tangent exclusion**: pangkas ±window titik dari tiap ujung cluster sebelum fit supaya titik segmen lurus tidak men-bias radius.
- Coverage ladder: `<30°` buang; `30–60°` kandidat + `review_reason: arc_coverage_low`; `≥60°` PASS-eligible (sebelumnya threshold 30°).

### 3.3 Endpoint virtual corner (mold line)

`refine_virtual_corners()`: endpoint tiap logical edge digeser ke **perpotongan garis fit dengan garis neighbor yang tegak-lurus** (±15° dari 90°) bila perpotongan wajar (≤ `virtual_corner_gap_px` 40px dari ujung support dan neighbor menjangkau titik tsb). Fallback: support min/max (perilaku lama). Field baru `endpoint_sources: ["virtual_intersection"|"support", ...]`. Semantik = mold line / virtual sharp (konvensi sheet metal).

### 3.4 Task baru `outer_dimension` (overall X/Y)

- Frame sumbu part dari arah fitted edge terpanjang; validasi dukungan (≥60% total panjang edge dalam ±6° dari axis atau axis+90°); fallback sumbu image berlabel `axis_source: "image"`.
- Kontur diproyeksikan ke metric space (anisotropik `scale_x/scale_y`) lalu dirotasi ke frame part; nilai = extent max−min per axis dengan **validasi dukungan ekstrem** (≥3 titik kontur dalam toleransi; spike 1–2 pixel ditolak).
- Response: `overall_candidates[]` `{id, axis, value_mm, axis_angle_deg, axis_source, points, confidence (0.85 edges / 0.6 image), geometry: {kind: "outer_extent", ...}}`.
- `measure_geometry("outer_dimension", [], calibration, geometry)` → `{value: value_mm, unit: "mm"}`.
- Readiness: `no_usable_edge` bila tidak ada kandidat. Verdict rules tidak berubah.

### 3.5 Frontend

- Checkbox task "Dimensi keseluruhan (X/Y)" (`outer_dimension`).
- Kartu kandidat Overall X/Overall Y (label, value_mm, confidence) → add item (mirror pola corner).
- Overlay garis dashed antara `geometry.points` + label.
- i18n: `measurement.taskOverall`, `selectOverallHint`, `overallX`, `overallY` (id + en).

## 4. Verifikasi

- Test invarian rotasi corner: rounded rect 0°/45°/90° — radius tiap estimasi 10–14 mm (true 12), spread ≤ 1.0 mm.
- Test Taubin > Kåsa pada arc 45° ber-noise; test lama `fit_circle` tetap hijau.
- Test endpoint virtual corner: endpoint edge top rounded rect snap ke corner (±3px).
- Test overall extent: X=100 mm, Y=80 mm ±1.0 pada fixture 0.5 mm/px; API test `task_types=["outer_dimension"]`.
- Full backend `pytest`, frontend `npm test` + `npm run build` tetap hijau (semua perubahan additive).
- **Evidence fisik (user):** dummy part baru dengan drawing lengkap (line, corner, bend, circle) di-capture 3 rotasi; bias + repeatability dicatat di milestones.

## 5. Out of scope

Guard band ISO 14253-1, subpixel edge localization, bias compensation per-station, Controlled Bench qualification.
