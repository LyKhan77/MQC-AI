# Inspect Measurement — 2D Geometry Improvement Design

**Status:** Approved for implementation planning
**Date:** 12 August 2026
**Target:** Prototype Slice 1–2
**Related:** [Prototype PRD](./inspect-measurement-prototype.md) · [Prototype Milestones](./inspect-measurement-prototype-milestones.md) · [Proper PRD](./inspect-measurement-proper.md) · [Station Design](./inspect-measurement-station-multiscale-design.md)

## 1. Goal

Improve top-down 2D measurement so inspector selects one meaningful geometry instead of manually adding fragmented LSD segments.

Target workflow:

`Capture → Calibrate X/Y → Choose checks → Process → Select geometry → Enter nominal/tolerance → Evaluate`

One component may contain multiple captured views. Camera remains top-down; inspector rotates component to expose each required face.

## 2. Scope

### Slice 1 — Reliable linear dimension

- Manual two-axis calibration: horizontal X and vertical Y.
- Merge fragmented line candidates into one logical edge.
- Fit one stable line from supporting edge pixels.
- Measure outer-to-outer projected dimension by default.
- Hide calibration/helper overlays after processing; allow independent show/hide.
- Preserve legacy one-line calibration for saved history.

### Slice 2 — Corner and bend geometry

- Optional multi-select checks in one process:
  - `Dimensi sisi (mm)`
  - `Radius corner (R mm)`
  - `Sudut bending (°)`
- Fit selected rounded corner from external contour points.
- Measure angle between two selected logical flange edges.
- Store selected geometry, result, tolerance, confidence, and review reason.

### Slice 3 — Later station work

- Station Preset tied to camera, resolution, fixed focus, working distance, and calibration artifact.
- Lens distortion correction and planar homography.
- Calibration expiration and verification checks.
- Physical repeatability and accuracy qualification.

## 3. Non-goals

- 3D reconstruction, depth, hidden inner geometry, or true material thickness from one pose.
- AI model training or inference.
- Automatic PASS without inspector selecting/confirming target geometry.
- PDF/CAD drawing comparison.
- Production accuracy claim before station qualification.

## 4. View and task model

Each captured image is one `InspectionView` with a required session `pose_type`:

- `TOP_FACE`: main planar length/width and hole layout.
- `REVERSE_FACE`: reversed planar face.
- `PROFILE_FACE`: component rotated so thickness/profile and bending flanges face camera.
- `CUSTOM_FACE`: another inspector-defined face.

Process keeps canonical `view_type`: `TOP_FACE`/`REVERSE_FACE` map to `top`, `PROFILE_FACE` maps to `profile`, and `CUSTOM_FACE` requires inspector-selected compatible type.

“Thickness” uses the same linear-dimension engine. It becomes a height/width measurement in `PROFILE_FACE`, not a separate 3D task.

New requests accept `task_types[]`. Existing `task_type` remains valid and maps to a one-item array.

## 5. Calibration contract

### 5.1 Recommended mode: independent reference

Inspector places a traceable rectangle, ruler, or calibration plate whose reference marks sit at the same height/measurement plane as the target surface.

1. Draw horizontal X line and enter known millimetres.
2. Draw vertical Y line and enter known millimetres.
3. System snaps each line to its assigned axis.
4. Process becomes PASS-eligible only when both axes validate.

Equations:

```text
scale_x = known_x_mm / reference_x_px
scale_y = known_y_mm / reference_y_px

length_mm = sqrt((dx_px * scale_x)^2 + (dy_px * scale_y)^2)
```

Validation:

- X reference must be within 10° of horizontal before snapping.
- Y reference must be within 10° of vertical before snapping.
- Known lengths must be positive.
- Reference lines must exceed the existing minimum pixel length.
- Calibration artifact and target surface must share one measurement plane.
- Recalibrate each staged capture when component rotation changes target-plane height; do not copy calibration between views unless the same valid reference remains visible on the same plane.

### 5.2 Demo mode: component as reference

Allowed for development. Result status stays `REVIEW`, because a component dimension used as calibration reference cannot independently verify the same dimension.

### 5.3 Legacy compatibility

Saved runs containing only `mm_per_pixel` remain readable. New processing may display them, but cannot produce a new PASS unless both X/Y scales exist or a valid future Station Preset supplies them.

Camera height and FOV are metadata only in Slice 1–2. They do not replace planar calibration.

## 6. Linear-dimension algorithm

### 6.1 Candidate extraction

1. Convert to grayscale and reduce noise.
2. Build an external component contour using threshold/edge evidence plus morphology; use the dominant closed contour or inspector-selected component when multiple objects exist.
3. Detect line segments with OpenCV `LineSegmentDetector` using `LSD_REFINE_ADV` when supported.
4. Retain segment width, precision, and NFA metadata where available.
5. Use `HoughLinesP` only as fallback/complement when LSD evidence is insufficient.

LSD segments are diagnostic candidates, not final measurements.

### 6.2 Logical-edge grouping

Group candidates only when all checks pass:

- similar orientation;
- small perpendicular distance between support lines;
- projected intervals overlap or have a bounded gap;
- compatible local edge-pixel support.

Do not merge nearby parallel edges from different physical boundaries. Thresholds remain backend constants for this prototype; expose diagnostics, not tuning controls, to inspector.

### 6.3 Robust line fit

Collect edge pixels in a narrow band around each candidate group. Fit one logical line with `cv.fitLine`, using robust distance (`DIST_HUBER` first; `DIST_WELSCH` fallback only if validation proves better).

One group returns:

- line origin and direction;
- supporting pixel count;
- residual;
- confidence;
- source candidate IDs.

### 6.4 Measurement semantics

Default inspector result is `outer_span`:

1. Inspector clicks a logical edge to choose measurement direction.
2. Project external component contour onto that direction.
3. Use minimum and maximum projections as outer endpoints.
4. Convert vector using X/Y calibration.

Rounded corners therefore contribute to full outer length/width. Inspector no longer adds E2 + E3 manually.

Optional Advanced result `straight_run` may expose the fitted straight section between tangent/support limits. It is diagnostic only in Slice 1–2 and must not replace default H/W.

## 7. Rounded-corner algorithm

When `Radius corner` is checked:

1. Build external component contour.
2. Inspector clicks or brushes the intended corner arc.
3. Select contour points around that arc.
4. Fit circle first; fit ellipse only as diagnostic fallback for perspective/segmentation warning.
5. Report outer radius, fit residual, arc coverage, and confidence.

Reject or mark `REVIEW` when arc coverage is too short, residual is high, or corner is occluded. Inner radius remains future drawing/recipe work.

## 8. Bend-angle algorithm

Available only when two flange boundaries are visible in a `PROFILE_FACE` view.

1. Inspector selects first logical flange edge.
2. Inspector selects second logical flange edge.
3. Extend fitted lines to a virtual intersection.
4. Orient each ray from the virtual intersection toward its selected flange support segment.
5. Return the angle between those rays in range `0–180°`.

This ray rule preserves obtuse bends; it does not always choose the acute line angle. Ambiguous support orientation produces `REVIEW`.

Default tolerance: `±0.5°`. Drawing-specific bend-angle conventions remain future recipe metadata; prototype label must explain that result is the included angle between selected visible flange rays.

## 9. Inspector UX

Inspector-facing language avoids LSD, Hough, NFA, contour, and fit terminology.

Main prompts:

- `Gambar garis referensi horizontal.`
- `Gambar garis referensi vertikal.`
- `Klik sisi yang ingin diukur.`
- `Pilih lengkungan.`
- `Pilih bidang pertama (1/2).`
- `Pilih bidang kedua (2/2).`
- `Konfirmasi sudut bagian komponen.`

Overlay layers after processing:

- `Hasil`: visible by default.
- `Referensi`: hidden by default; independent show/hide.
- `Garis bantu`: hidden by default; independent show/hide.

Changing overlay visibility never reprocesses the image. `Advanced` may show raw candidates, residual, confidence, and rejection reason.

## 10. API and persistence changes

### Calibration v2

```json
{
  "mode": "manual_axes",
  "source": "independent_artifact",
  "x": { "p1": [0, 0], "p2": [100, 0], "known_mm": 50.0 },
  "y": { "p1": [0, 0], "p2": [0, 120], "known_mm": 60.0 },
  "scale_x_mm_per_px": 0.5,
  "scale_y_mm_per_px": 0.5,
  "verdict_eligible": true
}
```

### Process request

```json
{
  "task_types": ["linear_dimension", "corner_radius", "bend_angle"],
  "view_type": "profile",
  "pose_type": "PROFILE_FACE",
  "calibration": {}
}
```

If `task_types` is absent, backend maps existing `task_type` into the array.

### Process response additions

- `logical_edges[]`
- `corner_arcs[]`
- `bend_candidates[]`
- `calibration_quality`
- existing raw candidates retained for backward compatibility and Advanced diagnostics

### Evaluation record additions

- geometry task type and selected geometry ID;
- nominal, lower/upper tolerance, measured value, unit;
- PASS/FAIL/REVIEW;
- calibration mode/source/version;
- residual/confidence and review reason;
- selected capture/view and operator identity;
- audit timestamps.

## 11. Review reasons

Use explicit codes and plain inspector messages:

- `reference_incomplete`
- `reference_not_axis_aligned`
- `reference_not_independent`
- `component_not_isolated`
- `edge_ambiguous`
- `edge_support_low`
- `arc_coverage_low`
- `arc_residual_high`
- `bend_flange_missing`
- `unsupported_pose`

No silent fallback may turn weak geometry into PASS.

## 12. Verification

### Automated synthetic checks

- Two fragmented collinear segments merge into one logical edge.
- Nearby parallel boundaries do not merge.
- Dual-axis conversion handles unequal X/Y scales.
- Rounded rectangle outer span uses contour extremes, not shortened straight LSD segments.
- Synthetic radius and bend fixtures return stable expected geometry.
- Legacy one-line saved record still opens.
- Multi-select request and old single-task request both process.
- Reference/helper overlay toggles do not change result data.

### Manual acceptance with existing captures

- `img5.png`: one selected vertical edge represents full outer height and one selected horizontal edge represents full outer width, without manual E2 + E3 addition. Existing component-reference calibration remains `REVIEW`; `59.5 × 49 mm` is comparison evidence, not independent calibration evidence.
- `img8.png` and `img9.png`: intended rounded corner can be selected and returns radius or explicit REVIEW reason.
- `img10.png`: two visible flange edges can be selected and return an included angle or explicit REVIEW reason.

These checks validate workflow, not production metrology. Final tolerances require Stage 1 station hardware, traceable artifact, repeated captures, and comparison against a calibrated physical instrument.

## 13. Implementation boundaries

- Reuse current OpenCV backend and canvas interaction patterns.
- No new ML dependency.
- No new UI library.
- No threshold controls in inspector UI.
- One shared logical-geometry pipeline serves Image, Live Camera, and Mobile Camera captures after staging.

## 14. OpenCV baseline

- [OpenCV 4.13 LineSegmentDetector](https://docs.opencv.org/4.13.0/db/d73/classcv_1_1LineSegmentDetector.html)
- [OpenCV 4.13 `fitLine` and shape analysis](https://docs.opencv.org/4.13.0/d3/dc0/group__imgproc__shape.html)
- [OpenCV 4.13 camera calibration](https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html)
