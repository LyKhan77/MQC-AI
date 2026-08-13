# PRD — Inspect Measurement Prototype

**Status:** Implemented multi-view prototype with I2/I3 geometry improvements; physical accuracy pending
**Date:** 12 August 2026
**Owner:** GSPE / MQC-AI

## 1. Keputusan ringkas

Prototype menggunakan alur vertical slice berikut:

```text
Create manual component/series session and stage Image / Live / Mobile views
  → Process one side
  → Tampilkan logical geometry + hasil ukuran
  → Inspector atur nominal dan toleransi per measurement item
  → Evaluate dimension
  → Simpan hasil + History + Audit Log
```

Prototype tidak mencoba menyelesaikan seluruh versi proper. Tujuannya membuktikan tiga hal: gambar dapat dikalibrasi menjadi mm, edge dapat diukur dengan bantuan OpenCV, dan hasil dapat dievaluasi per item tanpa model khusus untuk setiap komponen.

Improvement Slice 1–2 mengganti raw LSD segment sebagai hasil utama dengan logical edge, dual-axis calibration, selected corner radius, dan selected bend angle. Desain approved: [`inspect-measurement-2d-geometry-improvement-design.md`](./inspect-measurement-2d-geometry-improvement-design.md).

## 2. Masalah

Komponen berbeda-beda, jumlah sisi tidak tetap, dan belum ada aturan fixed dimension. Sistem perlu bekerja secara global dengan konfigurasi inspector, bukan dengan template model per part.

Auto-measurement penuh berisiko menghasilkan PASS palsu ketika edge tertutup, glare tinggi, perspektif miring, atau komponen memiliki beberapa bidang 3D. Karena itu prototype memakai pendekatan semi-otomatis: OpenCV menyarankan kandidat, inspector mengonfirmasi atau mengoreksi titik ukur.

## 3. Tujuan dan indikator berhasil

### Tujuan

- Mengukur satu sisi dari satu image.
- Menyimpan beberapa view dalam satu session dengan nama komponen/seri manual.
- Memproses hanya view yang dipilih setelah capture atau upload selesai.
- Menghasilkan ukuran dalam mm, bukan hanya pixel.
- Mendukung beberapa measurement item pada sisi yang sama.
- Mengatur nominal dan toleransi setiap item secara manual.
- Menghasilkan `PASS`, `FAIL`, atau `REVIEW`.
- Menyimpan hasil dengan nama seri/komponen manual.
- Menampilkan kembali hasil dari History dan mencatat aksi penting ke Audit Log.

### Indikator berhasil

- Inspector dapat menyelesaikan satu image dari upload sampai verdict tanpa konfigurasi model.
- Setiap item memiliki overlay, nilai measured, nominal, tolerance, min, max, deviation, dan status.
- Perubahan tolerance langsung mengubah verdict.
- Measurement tanpa kalibrasi valid tidak boleh berstatus `PASS`.
- Hasil tersimpan dan dapat dibuka kembali tanpa kehilangan image, calibration, edge, atau tolerance.
- Prototype dapat diuji menggunakan `temp/output-bending_gpt.png`.

## 4. Pengguna

**QC Inspector:** mengambil atau memilih satu image, memeriksa kandidat edge, mengisi nominal/tolerance dari drawing atau instruksi pilot, lalu menyimpan hasil.

Inspector tidak perlu memahami OpenCV. UI harus menjelaskan langkah dalam bahasa operasional: pilih image, kalibrasi, process, cek garis, isi tolerance, evaluate.

## 5. Scope prototype

### In scope

- Input satu atau beberapa image melalui file upload, satu atau beberapa frame dari registered Live Camera, atau beberapa frame dari Mobile Camera client.
- Live Camera menampilkan preview camera terdaftar dan memakai trigger capture; frame hasil capture masuk ke pipeline yang sama seperti upload.
- Mobile Camera memakai `getUserMedia()` browser pada HTTPS; inspector membuka preview lalu mengambil satu still frame ke pipeline yang sama.
- Nama run/seri/komponen diisi manual.
- Session memiliki dynamic custom views; inspector menambah view saat komponen diputar/reposition.
- Pose `TOP_FACE`/`REVERSE_FACE` untuk planar, `PROFILE_FACE` untuk thickness/bend guidance.
- Global/Detail measurement profile selector dengan resolution/camera/capability warning.
- Save/reopen/delete view dan completion guard untuk session.
- Kalibrasi manual horizontal X dan vertical Y pada bidang yang sama; legacy one-line calibration tetap dapat dibuka.
- Process server-side menggunakan OpenCV tanpa trained model.
- Kandidat garis/edge dari `LineSegmentDetector`; `HoughLinesP` hanya fallback/complement.
- Kandidat collinear digabung dan di-fit menjadi logical edge sebelum dipilih inspector.
- Multi-select `Dimensi sisi`, `Radius corner`, dan `Sudut bending` pada satu process.
- Pemilihan logical geometry oleh inspector; manual item fallback tersedia.
- Endpoint drag/click correction deferred sampai validasi UX/akurasi berikutnya.
- Measurement item minimal:
  - edge length / point-to-point linear dimension;
  - edge-to-edge linear dimension;
  - selected outer corner radius;
  - hole diameter atau hole-to-hole center distance jika lingkaran dapat dideteksi;
  - angle hanya jika dua line berada pada bidang image yang sama.
- Nominal dan tolerance per item.
- Default tolerance:
  - linear: `±2.0 mm`;
  - angle: `±0.5°`.
- Default tolerance, lalu override per item.
- Evaluation:
  - `PASS`: measured berada dalam `[nominal - tolerance, nominal + tolerance]`;
  - `FAIL`: measured berada di luar range;
  - `REVIEW`: kalibrasi invalid, edge confidence rendah, edge ambigu, atau geometry tidak cukup untuk dipercaya.
- Save result, History, detail result, dan Audit Log.
- Reuse Carbon tokens, i18n, API client, audit pattern, SQLite, dan `opencv-python-headless` yang sudah ada.

### Out of scope

- Live Camera continuous auto-measurement atau continuous video processing; prototype hanya preview + one-shot trigger capture.
- Fixed required view checklist; prototype memakai dynamic custom views tanpa jumlah sisi fixed.
- QC Station hardware workflow.
- CAD/PDF import, OCR drawing, automatic callout mapping, atau CAD parsing.
- Automatic source-of-truth recipe dari drawing.
- True 3D thickness atau bend angle dari satu top-down image.
- Trained model, per-part model, object detector, atau AI generatif.
- Production accuracy claim sebelum calibration validation.

## 6. Constraint measurement

### Kalibrasi wajib

Pixel hanya dapat diubah menjadi mm jika ada skala. Flow baru memakai dua reference axis:

1. Inspector menggambar reference horizontal X dan memasukkan panjang aktualnya.
2. Inspector menggambar reference vertical Y dan memasukkan panjang aktualnya.
3. Sistem menghitung `scale_x_mm_per_px` dan `scale_y_mm_per_px`.
4. Reference independen pada measurement plane menghasilkan PASS-eligible calibration.
5. Komponen boleh dipakai sebagai reference untuk demo, tetapi hasil tetap `REVIEW`.

Untuk jig development empat titik hijau, tombol `Deteksi 4 titik jig` hanya menemukan centroid dan membuat garis X/Y. Inspector tetap memasukkan panjang fisik X dan Y manual; pixel tidak dapat menentukan mm tanpa nilai fisik tersebut. Bila deteksi gagal, inspector kembali memakai `Gambar horizontal (X)` dan `Gambar vertical (Y)`.

Titik calibration membawa ukuran coordinate-space preview ke backend. Backend menormalisasi titik ke frame OpenCV sebelum menghitung scale dan mengembalikan titik frame final; canvas tidak melakukan rescale kedua kali setelah process.

Jika reference tidak tersedia atau scale error melewati batas validasi, sistem menampilkan ukuran dalam status `REVIEW`, bukan memberi `PASS`.

Legacy saved run dengan `mm_per_pixel` tetap dapat dibuka. Kalibrasi per-image cukup untuk improvement ini. Versi proper menambah station profile, intrinsic camera calibration, lens distortion correction, ChArUco/marker, dan homography desk plane.

### Peran OpenCV

Pipeline kandidat:

1. Decode image dan validasi ukuran.
2. Grayscale, denoise, dan contrast normalization seperlunya.
3. Canny/gradient untuk edge map.
4. Line-segment candidate dari `LineSegmentDetector` refined; `HoughLinesP` fallback/complement.
5. Kelompokkan segment collinear berdasarkan angle, jarak support line, projected overlap/gap, dan local pixel support.
6. Fit satu logical edge memakai robust `cv.fitLine`.
7. Untuk H/W default, proyeksikan external component contour agar rounded corner tetap masuk outer-to-outer dimension.
8. Kembalikan logical geometry, residual, confidence, dan source candidates.
9. Inspector memilih logical geometry; raw candidates hanya muncul pada `Advanced`.

Line-segment detection membantu menemukan garis, tetapi bukan source of truth. Toleransi, occlusion, glare, perspective, dan edge selection tetap membutuhkan verifikasi inspector.

### Batasan geometri

- Panjang/lebar pada bidang yang sejajar dengan camera plane dapat diukur.
- Hole diameter/pitch hanya valid jika bentuk hole terlihat cukup jelas dan distorsi sudah dikoreksi atau masih dalam batas validasi.
- Ketebalan tidak dapat dipercaya dari top-down image; butuh side/profile view atau metode lain.
- Bend angle 3D tidak dapat disimpulkan secara akurat dari satu top-down image; angle prototype hanya untuk dua line pada bidang image yang sama.

## 7. Model measurement item

Setiap item disimpan sebagai data, bukan hanya label di canvas:

```json
{
  "id": "E1",
  "type": "edge_length",
  "label": "Overall length",
  "geometry": {
    "points": [[120, 80], [820, 80]],
    "units": "px"
  },
  "measured": 142.4,
  "unit": "mm",
  "nominal": 140.0,
  "tolerance": 2.0,
  "min": 138.0,
  "max": 142.0,
  "deviation": 2.4,
  "confidence": 0.91,
  "status": "FAIL"
}
```

Nominal wajib diisi sebelum evaluate. Prototype menerima nominal secara manual. Drawing tetap menjadi source of truth secara manusia; import drawing dan recipe mapping masuk fase proper.

## 8. UX yang ditargetkan

Measurement Studio memakai pola tiga area yang mengadopsi QC Studio:

- **Left:** input image, nama run, calibration state, recent/history.
- **Center:** image canvas, logical geometry, selected result overlay, optional reference/helper layers, zoom/pan controls.
- **Right:** measurement item table, measured/nominal/tolerance, status, Evaluate, Save.
- Panel input dan evaluate cukup lebar untuk label serta form fields; canvas memakai satu image frame bersama untuk image dan SVG supaya overlay tetap tepat saat fit, zoom, dan pan.

Flow UI:

1. Upload image, pilih Live Camera, atau pilih Mobile Camera; lalu isi nama run.
2. Jika Live Camera, buka preview dan klik `Trigger capture`.
3. Jika Mobile Camera, izinkan akses browser, buka preview, lalu klik `Capture`.
4. Gambar reference horizontal X dan vertical Y, atau gunakan `Deteksi 4 titik jig`; isi panjang fisik X dan Y manual.
5. Pilih satu atau beberapa check: dimensi sisi, radius corner, dan sudut bending.
6. Klik `Process measurement`.
7. Sistem menampilkan logical geometry.
8. Inspector memilih geometry target, lalu menambah item lain bila perlu.
9. Inspector mengisi nominal dan tolerance per item.
10. Klik `Evaluate dimension`.
11. Sistem menampilkan summary `PASS/FAIL/REVIEW` dan alasan non-pass.
12. Klik `Save measurement`.

Canvas controls mengikuti QC Studio: wheel atau tombol zoom pada range `50%–500%`, drag untuk pan, dan `Reset` untuk kembali ke fit awal. Kontrol ini tersedia sebelum process agar calibration presisi. Saat menggambar, crosshair dash opacity rendah membantu alignment. Mobile Camera menampilkan crosshair tengah sebagai guide positioning dan tidak menulis overlay ke capture. `Reset workspace` membersihkan media staged dan state lokal tanpa menghapus History/Audit. Candidate edge memakai outline/halo kontras, endpoint marker, dan selected measurement label yang lebih besar agar terbaca di atas komponen.

`Tambah edge manual` tidak tersedia: implementasi lama membuat garis dummy dan bukan memperbaiki LSD. Fallback click-start/click-end untuk edge `REVIEW` ditunda sampai contour fallback otomatis tervalidasi.

UI harus mencegah evaluate sebelum image processed, calibration valid, geometry valid, dan nominal/tolerance lengkap.

## 9. Persistence dan audit

Prototype menyimpan satu `MeasurementRun` dengan:

- manual name;
- timestamp, user, source filename/type;
- original image reference;
- calibration data;
- processing metadata dan candidate method;
- measurement items lengkap;
- summary verdict.

Audit actions minimum:

- `MEASUREMENT_PROCESSED`;
- `MEASUREMENT_EVALUATED`;
- `MEASUREMENT_SAVED`;
- `MEASUREMENT_DELETED`.

History dapat search berdasarkan nama dan filter verdict. Delete memakai confirmation dan menghapus metadata serta file measurement yang dimiliki run.

## 10. Source of truth dan tolerance

Prototype belum membaca PDF/CAD. Inspector memasukkan `nominal` dan `tolerance` dari drawing secara manual. Ini sengaja: masalah measurement engine dan evaluation dapat divalidasi lebih awal tanpa memasukkan parser drawing yang kompleks.

Versi proper dapat menambahkan `Measurement Recipe` dari drawing:

```text
drawing revision → feature ID → expected view/datum → nominal → tolerance → measurement item
```

Saat recipe tersedia, inspector hanya memilih recipe; measured result dibandingkan dengan nominal/tolerance recipe. Revision drawing wajib ikut tersimpan di audit.

## 11. Milestone

Estimasi untuk satu developer yang sudah memahami codebase. Milestone dapat berjalan berurutan karena M1 menjadi dasar M2 dan M3.

| Milestone | Isi | Exit criteria | Estimasi |
|---|---|---|---:|
| M0 — Contract & calibration | Final data shape, status rules, manual scale calibration, synthetic test fixtures | Measurement item dan verdict contract disetujui; test fixture dapat menghasilkan scale yang benar | 0.5–1 hari |
| M1 — OpenCV measurement kernel | Decode, preprocessing, line candidates, endpoint geometry, px-to-mm, confidence/review gate | Service mengembalikan kandidat stabil dan math linear/angle lulus unit test | 2–3 hari |
| M2 — Backend vertical slice | Process upload, file serving, MeasurementRun persistence, list/detail/delete, audit | API dapat process → save → reload → delete dengan TestClient | 2–3 hari |
| M3 — Measurement Studio input/process | Route, upload, calibration interaction, canvas overlay, process state/error state | Inspector dapat upload dan melihat hasil candidate pada `output-bending_gpt.png` | 2–3 hari |
| M4 — Tolerance & evaluate | Editable item table, per-item tolerance, defaults, nominal, PASS/FAIL/REVIEW summary | Satu perubahan tolerance mengubah status item dan summary secara benar | 1–2 hari |
| M5 — History & audit UX | Saved run list, reopen detail, delete confirmation, audit entries, bilingual labels | Saved result dapat ditemukan dan dibuka kembali; audit lengkap | 1–2 hari |
| M6 — Accuracy gate | Reference samples, repeatability check, glare/pose/scale failure cases, browser/API regression | Prototype report error; tidak ada klaim ±2 mm atau ±0.5° tanpa evidence station | 2–3 hari |
| I2 — Logical edge + calibration v2 | Dual-axis reference, line grouping, robust fit, outer-span result, overlay layers | `img5` tidak membutuhkan penjumlahan raw segment manual | 2–4 hari |
| I3 — Corner + bend geometry | Selected arc fit, selected flange-pair angle, multi-select checks | Synthetic fixtures stabil; capture nyata memberi result atau explicit `REVIEW` | 2–4 hari |

**Baseline prototype:** sekitar 10–14 hari kerja. Improvement I2–I3 menambah estimasi 4–8 hari kerja, belum termasuk hardware QC Station dan source-of-truth drawing integration.

Tracking implementasi tersedia di [`inspect-measurement-prototype-milestones.md`](./inspect-measurement-prototype-milestones.md). Dokumen tersebut menjadi checkpoint hidup: milestone hanya boleh berstatus `DONE` jika evidence implementasi dan verification tersedia.

## 12. Acceptance criteria

- [x] Satu image dapat diproses tanpa trained model.
- [x] Live Camera dapat menampilkan preview dan menghasilkan satu captured frame melalui trigger.
- [x] Mobile Camera dapat membuka preview HTTPS dan menghasilkan satu captured frame melalui browser client.
- [x] Calibration reference menghasilkan nilai `mm_per_pixel` yang terlihat dan tersimpan.
- [x] Canvas menampilkan candidate edge dan measurement geometry.
- [x] Inspector dapat menambah dan memilih measurement item; endpoint correction ditunda.
- [x] Setiap item memiliki nominal, tolerance, min, max, deviation, dan status.
- [x] Default linear `±2.0 mm`; angle `±0.5°` tersedia di kernel contract.
- [x] Invalid calibration/ambiguous edge menghasilkan `REVIEW`.
- [x] PASS hanya muncul setelah nominal, tolerance, geometry, dan calibration valid.
- [x] Save/reopen mempertahankan image, calibration, geometry, measurement, tolerance, dan verdict.
- [x] History dan Audit Log memuat aktivitas measurement.
- [x] `npm run build`, `npm test`, dan backend `pytest -v` lulus.
- [ ] Dual-axis calibration X/Y tersimpan dan menjadi syarat PASS untuk process baru.
- [ ] Satu logical edge menggantikan penjumlahan E2 + E3 manual pada workflow `img5`.
- [ ] Reference dan helper overlays tersembunyi default setelah process serta dapat di-toggle.
- [ ] Rounded corner dan bend angle dapat dipilih atau menghasilkan alasan `REVIEW` eksplisit.

## 13. Risiko dan keputusan upgrade

| Risiko | Dampak | Mitigasi prototype | Upgrade proper |
|---|---|---|---|
| Perspective/lens distortion | Ukuran edge meleset | Reference scale pada bidang sama + `REVIEW` gate | Intrinsic calibration, distortion correction, homography |
| Glare/background noise | Kandidat edge salah | Controlled image, preprocessing, manual correction | Fixed lighting, desk matte, background model, fixture |
| 3D bent component | Top-down projection menipu | Batasi prototype ke planar geometry | Dynamic views, profile camera, 3D reconstruction/fixture |
| Edge ambiguity | PASS palsu | Inspector confirmation + confidence gate | Part recipe/datum + validated auto-selection |
| Tolerance terlalu longgar/ketat | Verdict tidak bermakna | Manual per-item tolerance, audit perubahan | Recipe dari drawing revision |

## 14. Referensi teknis

- [OpenCV Camera Calibration](https://docs.opencv.org/4.13.0/dc/dbb/tutorial_py_calibration.html)
- [OpenCV ChArUco Calibration](https://docs.opencv.org/4.13.0/da/d13/tutorial_aruco_calibration.html)
- [OpenCV Perspective Transform](https://docs.opencv.org/4.13.0/da/d54/group__imgproc__transform.html)
- [OpenCV Homography](https://docs.opencv.org/4.13.0/d9/dab/tutorial_homography.html)
- [OpenCV Shape Analysis](https://docs.opencv.org/4.13.0/d3/dc0/group__imgproc__shape.html)
