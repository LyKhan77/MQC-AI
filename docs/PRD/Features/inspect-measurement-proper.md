# PRD — Inspect Measurement Proper Version

**Status:** P1-P2 and 2D geometry software slice implemented; station accuracy, drawing recipe, and profile metrology planned
**Date:** 12 August 2026
**Related prototype:** [`inspect-measurement-prototype.md`](./inspect-measurement-prototype.md)
**Milestone tracker:** [`inspect-measurement-proper-milestones.md`](./inspect-measurement-proper-milestones.md)
**Approved 2D improvement:** [`inspect-measurement-2d-geometry-improvement-design.md`](./inspect-measurement-2d-geometry-improvement-design.md)

## 1. Vision

Inspect Measurement menjadi task-driven Measurement Studio untuk QC Station. Inspector memberi nama seri komponen secara manual, mengambil beberapa foto dari sisi berbeda, memilih task measurement yang relevan, membandingkan hasil dengan drawing/source of truth, lalu menyimpan evidence lengkap untuk History dan Audit.

Prototype membuktikan measurement kernel dan session multi-view pada image/frame. Versi proper menambahkan station calibration tervalidasi, task/feature recipe, deterministic hole geometry, drawing recipe, profile/3D measurement strategy, dan review governance.

## 2. Target workflow

```text
Create inspection session
  -> Manual component/series name
  -> Select input: Image / Live Camera / Mobile Camera / Server Camera
  -> Capture or upload one or more views into staged frames
  -> Label dynamic custom view
  -> Calibrate station/view
  -> Draw reference line
  -> Process measurement candidates
  -> Confirm or correct geometry
  -> Apply drawing measurement recipe
  -> Evaluate per feature and per view
  -> Rotate/reposition component for next face
  -> Capture next required view
  -> Complete session
  -> Save History + Audit + evidence
```

Jumlah view tidak fixed. Inspector menambah view hanya jika sisi/feature berikutnya perlu diperiksa.

## 3. Users and operating context

### QC Inspector

Inspector bukan operator computer vision. UI harus memberi instruksi sederhana: `Place side`, `Trigger capture`, `Select view`, `Check edge`, `Evaluate`, dan `Next view`.

### QC Pilot / Quality Engineer

Pilot menyiapkan station profile, drawing recipe, datum, tolerance, expected view, dan acceptance rule. Pilot juga memvalidasi repeatability sebelum feature dipakai sebagai quality gate.

### QC Station

- Fixed top-down camera di atas desk matte untuk planar measurements.
- Controlled lighting dan fixed focus/exposure/white balance.
- Camera registration, station identity, resolution, lens, dan calibration revision disimpan.
- Trigger capture menghasilkan satu evidence frame per view.
- Inspector memutar/reposition komponen di desk matte; jumlah view tidak fixed.
- Rotasi horizontal pada bidang desk tetap face yang sama; membalik komponen memilih face baru.
- Free tilt/lift tidak diterima sebagai measurement valid.

Top-down station tidak cukup untuk semua dimensi. Ketebalan dan true 3D bend angle memerlukan profile camera, calibrated multi-camera, structured light, laser gauge, atau fixture measurement yang sesuai.

## 4. Proper scope

### 4.1 Session and dynamic views

- Manual session/series naming karena komponen tidak memiliki SN.
- One component session memiliki banyak view.
- View label bebas: `top`, `front`, `left flange`, `bend profile`, atau label pilot.
- View order dan jumlah view tidak fixed.
- Setiap view menyimpan source frame, camera/source, calibration revision, selected geometry, result, dan operator note.
- Session dapat incomplete dengan alasan; sistem tidak menganggap semua part memiliki view yang sama.

Software slice saat ini menyediakan `MeasurementSession`, dynamic staged view cards, save/delete view, reopen, completion guard, History, dan Audit. Session tidak boleh selesai ketika masih ada staged view yang belum disimpan.

### 4.1.1 Global and Detail measurement profiles

- `GLOBAL`: coverage komponen besar sampai sekitar 2100 mm; tidak otomatis mendukung feature 1 mm.
- `DETAIL`: area lebih kecil dengan resolusi lebih tinggi untuk feature kecil, hole, dan edge refinement.
- Profile menyimpan station/camera binding, resolution, FOV/working distance, calibration, revision, capability range, dan status validasi.
- Frame resolution dan camera binding wajib cocok dengan profile; mismatch menghasilkan `REVIEW`.
- Profile tidak boleh mengklaim support jika capability minimum/maksimum tidak tersedia.
- Satu development camera pada dua jarak/scale hanya untuk eksperimen; production disarankan dual fixed top-down camera atau setup optik tervalidasi.

### 4.2 Input sources

- Image upload.
- Live Camera/server camera preview + trigger capture.
- Mobile Camera melalui HTTPS jika deployment memerlukan inspeksi on-demand.
- Server Camera yang terdaftar di Settings.

Semua source menghasilkan canonical `InspectionView`. Measurement engine tidak perlu tahu apakah frame berasal dari upload atau camera.

### 4.3 Station calibration

Calibration dikelola sebagai profile, bukan angka sementara di UI:

- camera intrinsic matrix;
- lens distortion coefficients;
- ChArUco/checkerboard calibration result;
- desk-plane homography;
- physical scale and unit;
- station/camera/resolution/focus metadata;
- calibration date, operator, revision, and validation result.

Capture ditolak atau diberi `REVIEW` jika station profile invalid, resolution berbeda, marker tidak terbaca, atau calibration sudah expired menurut policy. Current P1 uses drawn reference-line calibration; automatic station matrix/homography application waits for validated station evidence.

### 4.4 Measurement engine

Engine menggunakan pipeline berlapis:

1. OpenCV candidate generation: refined LSD, Hough fallback/complement, contours, circles/ellipse, morphology, and edge quality.
2. Geometry refinement: collinear grouping, robust `cv.fitLine`, outer-contour projection, circle/ellipse fit, homography correction, and deterministic geometry.
3. Optional AI assistance: component/feature segmentation atau semantic edge selection.
4. Final measurement tetap dihitung dari calibrated geometry, bukan confidence AI.

Supported capability menggunakan task type eksplisit:

| Task type | Geometry | Minimum view | Proper rule |
|---|---|---|---|
| `linear_dimension` | line/edge-to-edge/point-to-point | `top` atau `profile` | Menghasilkan panjang/lebar dalam mm. |
| `thickness_profile` | dua edge parallel | `profile`/`side` | Tidak boleh PASS dari top-down view. |
| `bend_angle` | dua line/face angle | `profile` | Membutuhkan profile plane atau calibrated multi-view. |
| `inclination` | line terhadap datum axis | `top` atau `profile` | Datum/reference axis wajib tersedia. |
| `corner_radius` | selected external contour arc | `top` atau `profile` | Default result adalah outer radius; weak arc fit menjadi REVIEW. |
| `hole_diameter` | circle center + radius | `top` | Image harus di-undistort dan di-rectify bila perspektif ada. |
| `hole_center_distance` | center-to-center | `top` | Untuk pitch/bolt pattern. |
| `hole_edge_distance` | center distance minus radii | `top` | Jarak clear edge-to-edge antar lubang. |
| `hole_center_to_edge` | hole center ke component edge | `top` | Jarak center lubang ke edge komponen. |

Hole pipeline proper:

```text
undistort + planar rectify
  -> HoughCircles (candidate center)
  -> ROI contour/edge extraction
  -> fitEllipse or contour-derived radius
  -> center/radius confidence
  -> diameter, pitch, edge distance geometry
```

OpenCV 4.13 documents `HOUGH_GRADIENT_ALT`, `fitEllipse`, contour moments, and `LineSegmentDetector.detect()` metadata (`width`, `prec`, `nfa`). Hough circle radius remains a candidate, not the final authority; final diameter uses the refined contour/ellipse geometry. OpenCV has no single industrial metrology module, so the proper engine composes calibrated deterministic primitives.

Setiap result membawa `method`, `calibration_revision`, `confidence`, `repeatability_class`, dan `review_required`.

### 4.5 Drawing/source of truth

Drawing menjadi source of truth melalui `Measurement Recipe`:

```text
drawing revision
  -> feature ID / callout
  -> measurement type
  -> nominal
  -> tolerance
  -> datum/reference
  -> expected view
  -> method and unit
```

Tahap awal proper tetap menggunakan manual mapping dari PDF/CAD. Setelah format dan kebutuhan stabil, parser dapat ditambahkan secara bertahap:

- PDF callout extraction/OCR sebagai assistant, bukan authority tanpa review.
- DXF/STEP feature extraction jika format CAD pilot konsisten.
- Human approval wajib sebelum recipe aktif sebagai quality gate.

Drawing revision, recipe revision, dan mapping reviewer ikut tersimpan pada hasil.

### 4.6 Tolerance and evaluation

- Tolerance default hanya fallback, bukan rule universal.
- Recipe tolerance menjadi prioritas.
- Inspector dapat override hanya jika policy mengizinkan; override wajib alasan dan audit.
- Linear, angle, hole, thickness, dan bend memiliki unit/rule berbeda.
- Evaluation status: `PASS`, `FAIL`, `REVIEW`, `NOT_MEASURED`, `NOT_APPLICABLE`.
- `REVIEW` muncul untuk calibration invalid, ambiguous edge, low confidence, occlusion, out-of-view, atau unsupported geometry.
- Session summary tidak boleh `PASS` jika required view/feature belum selesai.

## 5. Studio UX

### Left rail — Session and views

- Session name dan component series name.
- Source selection.
- Dynamic view list.
- View completion state.
- Required/optional marker dari recipe.
- Calibration status.
- Measurement task selector with plain-language labels: `Length / Width`, `Thickness (Profile)`, `Bend Angle (Profile)`, `Inclination`, `Hole Diameter`, `Hole Pitch`, and `Hole Edge Distance`.
- Unsupported view/task combinations are blocked with an operational explanation, not a technical error.

### Center — Inspection canvas

- Live preview atau captured frame.
- Candidate edge overlay.
- Selected measurement geometry.
- Hole candidate overlays with center crosshair, circle/ellipse boundary, diameter label, and candidate confidence.
- Datum/reference overlay.
- Drawing callout/feature ID.
- Clear `Place next side` instruction.

### Right rail — Measurement and verdict

- Feature list from recipe.
- Measured, nominal, tolerance, min/max, deviation, confidence.
- Per-feature status and reason.
- Evaluate view / Evaluate session.
- Manual correction with audit reason.

### Inspector simplicity rules

- Default flow hides OpenCV terminology.
- `Advanced diagnostics` may show LSD/Hough source, pixel geometry, calibration residual, and confidence.
- Camera capture uses one prominent trigger button.
- Next-view action does not require a fixed checklist when the session is custom.
- Incomplete session explains exactly which view/feature remains.

## 6. Persistence and audit

Proper model hierarchy:

```text
MeasurementSession
  └── MeasurementView[]
        └── MeasurementResult[]
              └── RecipeFeature / DrawingRevision reference
```

Persist:

- manual series/session name;
- inspector, station, camera, and source;
- all original frames and processed evidence;
- dynamic view labels and order;
- task type, required view, geometry schema, detection method, and feature identity;
- calibration profile/revision;
- drawing/recipe revision;
- geometry, measured values, tolerance, confidence, and statuses;
- correction reason, notes, and final approval.

Audit minimum:

- session created/renamed;
- view captured/deleted/reordered;
- calibration selected/changed;
- measurement geometry corrected;
- tolerance or nominal overridden;
- view/session evaluated;
- result approved/rejected;
- drawing/recipe revision changed.

## 7. Software contract delivered by current slice

Session/profile endpoints:

```text
POST/GET/PATCH/DELETE /api/measurement-profiles[/{profile_id}]
POST/GET              /api/measurement-sessions
GET/PATCH/DELETE      /api/measurement-sessions/{session_id}
POST/DELETE           /api/measurement-sessions/{session_id}/views[/{view_id}]
```

Process metadata includes `view_label`, `pose_type`, and `scale_profile_id`. Pose rules:

| Pose | Supported checks |
|---|---|
| `TOP_FACE`, `REVERSE_FACE` | length/width, inclination, hole geometry on planar face |
| `PROFILE_FACE` | thickness and bend/profile checks |
| `CUSTOM_FACE` | saved label; task capability requires explicit approval |

`TOP_FACE` is not accepted as a valid thickness/bend pose. Invalid profile, camera/resolution mismatch, unsupported pose, and insufficient capability return `REVIEW`.

## 8. Accuracy and validation strategy

Accuracy is a station property, not only an algorithm property.

Validation levels:

1. **Algorithm test:** synthetic lines, circles, angles, and known transforms.
2. **Bench test:** calibrated reference artifact across image positions and orientations.
3. **Repeatability:** repeated captures without moving the part.
4. **Reproducibility:** different inspectors, sessions, and approved stations.
5. **Production pilot:** real component variation, glare, contamination, and borderline tolerance.

The system reports measured error and repeatability before enabling a dimension as an automatic quality gate. `±2 mm` linear and `±0.5°` angle are configuration defaults only; they are not accuracy guarantees.

## 9. Future improvement phases

| Phase | Improvement | Exit gate |
|---|---|---|
| P1 | Station profile contract, interactive reference calibration, fixed lighting, marker/homography foundation, planar task types, hole center/diameter/pitch candidates | Software vertical slice implemented; station matrix/homography runtime requires approved calibration evidence |
| P2 | Session + dynamic custom views + Live Camera trigger workflow | **Software slice implemented:** arbitrary side count, staged Image/Live/Mobile inputs, session/profile APIs, save/reopen/audit evidence. Physical station validation remains open. |
| P2.1 | Dual-axis calibration + logical planar geometry | Approved design implemented; inspector selects stable edge/corner/bend geometry instead of raw segments |
| P3 | Drawing revision + Measurement Recipe + manual mapping | Results compare against approved source-of-truth feature IDs |
| P4 | Profile/multi-camera strategy for thickness and bend angle | 3D dimensions have hardware-specific validation evidence |
| P5 | AI-assisted segmentation/semantic edge selection | False-edge rate improves without changing deterministic measurement authority |
| P6 | Approval policy, reports, station monitoring, drift detection | Measurement can operate as controlled QC quality gate |

## 10. Explicit non-goals

- One universal AI model that understands every component without calibration.
- Inferring thickness or 3D bend angle reliably from one top-down photo.
- Treating PDF OCR output as an approved dimension without human review.
- Using default tolerance as a substitute for engineering drawing requirements.
- Declaring high accuracy before station validation.

## 11. Open decisions before implementation

- Which camera model/resolution/lens becomes the first approved QC Station?
- Is the first proper station planar-only or includes a profile camera?
- Which drawing format is authoritative: PDF, DXF, STEP, or controlled export?
- Who may approve recipe/tolerance overrides?
- How long calibration remains valid and what triggers recalibration?
- Which measurement failures require automatic reject versus inspector review?

## 12. OpenCV implementation baseline

The current proper baseline follows the stable OpenCV 4.13.0 documentation:

- Camera setup: `calibrateCamera`/`calibrateCameraROExtended`, `undistort`, and `initUndistortRectifyMap`.
- Planar correction: `findHomography`, `getPerspectiveTransform`, `perspectiveTransform`, and `warpPerspective`.
- Lines: `LineSegmentDetector` with refinement metadata, then `HoughLinesP` fallback.
- Holes: `HoughCircles` with `HOUGH_GRADIENT_ALT` for candidates, followed by contour/moments and `fitEllipse` refinement.

References: [OpenCV calib3d 4.13](https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html), [OpenCV HoughCircles](https://docs.opencv.org/4.13.0/javadoc/org/opencv/imgproc/Imgproc.html), [OpenCV shape analysis](https://docs.opencv.org/4.13.0/d3/dc0/group__imgproc__shape.html), [OpenCV LineSegmentDetector](https://docs.opencv.org/4.13.0/db/d73/classcv_1_1LineSegmentDetector.html).
