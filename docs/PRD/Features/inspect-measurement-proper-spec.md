# Inspect Measurement Proper — P1 Specification

**Status:** Implementation specification; P1-P2 software slice implemented
**Date:** 11 August 2026
**Parent PRD:** [`inspect-measurement-proper.md`](./inspect-measurement-proper.md)

## Scope

P1 delivers a calibrated planar measurement vertical slice without claiming 3D accuracy:

- Interactive reference-line calibration.
- Explicit task type and expected view.
- Planar line dimensions.
- Hole candidate detection with center and radius evidence.
- Hole diameter, center-to-center, hole edge-to-edge, and hole center-to-part-edge geometry.
- `REVIEW` for invalid calibration, unsupported view, ambiguous candidates, and low confidence.
- One named `MeasurementSession` can contain dynamic staged views from Image, Live Camera, and Mobile Camera.
- Global/Detail `MeasurementProfile` selection is additive; unbound manual reference-line calibration remains supported.

Thickness and bend remain profile-view contracts. They must not be evaluated as valid top-down measurements.

## Canonical task types

```text
linear_dimension
thickness_profile
bend_angle
inclination
hole_diameter
hole_center_distance
hole_edge_distance
hole_center_to_edge
```

Task metadata:

```json
{
  "id": "H01",
  "type": "hole_diameter",
  "label": "Bolt hole diameter",
  "view_type": "top",
  "nominal": 10.0,
  "tolerance": 0.2,
  "unit": "mm",
  "required": true,
  "geometry": {
    "kind": "circle",
    "center": [412.5, 238.2],
    "radius_px": 26.4
  }
}
```

## Geometry contracts

| Geometry | Payload | Output |
|---|---|---|
| Line | `points: [[x1,y1],[x2,y2]]` | length, angle, unit |
| Angle | `lines: [[[x1,y1],[x2,y2]], [[x3,y3],[x4,y4]]]` | degrees |
| Circle | `center: [x,y]`, `radius_px` | diameter, center |
| Circle pair | `feature_a`, `feature_b` circle refs | center distance or edge distance |
| Circle-to-edge | circle ref + line ref | center-to-edge distance |

Existing prototype `points` remains accepted for backwards compatibility. New proper results carry `geometry` and `task_type`.

## Calibration contract

Interactive capture calibration:

```json
{
  "mode": "reference_line",
  "point_a": [120.0, 580.0],
  "point_b": [520.0, 580.0],
  "known_mm": 50.0,
  "reference_px": 400.0,
  "mm_per_pixel": 0.125,
  "valid": true
}
```

Station calibration extension:

```json
{
  "mode": "station_profile",
  "station_id": "QC-STATION-01",
  "camera_id": "cam-top-01",
  "revision": "cal-2026-08-10-01",
  "image_size": [1920, 1080],
  "camera_matrix": [],
  "distortion_coefficients": [],
  "homography": [],
  "validation": {"status": "valid", "reprojection_error_px": 0.0}
}
```

P1 stores the station-profile shape and supports reference-line calibration. Automatic marker/homography application is enabled only when a valid matrix/profile exists.

## Process contract

`POST /api/measurements/capture` stages a server-camera frame without running detection. The response returns `source_key`, frame dimensions, and frame URL.

`POST /api/measurements/process` accepts:

- `task_type`: canonical task type, default `linear_dimension`.
- `view_type`: `top`, `profile`, or `side`, default `top`.
- `calibration`: reference-line or station profile JSON.
- `options`: detector options.
- `source_key`: staged Live Camera frame key; mutually exclusive with upload/camera capture.

Session/profile contract:

```text
POST/GET/PATCH/DELETE /api/measurement-profiles[/{profile_id}]
POST/GET              /api/measurement-sessions
GET/PATCH/DELETE      /api/measurement-sessions/{session_id}
POST/DELETE           /api/measurement-sessions/{session_id}/views[/{view_id}]
```

`MeasurementRun` accepts additive `session_id`, `view_label`, `pose_type`, `scale_profile_id`, and `view_status` metadata. A session summary contains `status`, `view_count`, `pass`, `fail`, and `review`. Completion returns conflict when no view is saved or when staged views remain unsaved.

Profile validation requires valid/approved status, matching configured resolution, optional camera binding match, and positive reference-line scale. Capability ranges are explicit: a profile with `minimum_supported_feature_mm: 8` cannot claim support for a 1 mm nominal feature. Global and Detail profiles never mix silently because the selected profile ID and revision are persisted on each view.

Pose rules:

| `pose_type` | Allowed prototype tasks |
|---|---|
| `TOP_FACE`, `REVERSE_FACE` | planar length/width, inclination, hole geometry |
| `PROFILE_FACE` | thickness/profile and bend |
| `CUSTOM_FACE` | review-only until capability is configured |

Top-down camera remains fixed. Inspector rotates/repositions the component; free tilt/lift returns `REVIEW` at the station policy layer.

Response adds:

```json
{
  "task_type": "hole_diameter",
  "view_type": "top",
  "view_label": "top face",
  "pose_type": "TOP_FACE",
  "scale_profile_id": "detail-qc-01-r2",
  "holes": [
    {
      "center": [412.5, 238.2],
      "radius_px": 26.4,
      "diameter_px": 52.8,
      "confidence": 0.93,
      "source": "hough_circle_alt"
    }
  ]
}
```

## Detection policy

1. Undistort/rectify when station calibration supplies the required matrices.
2. Run task-specific candidate generation.
3. Refine geometry with deterministic contour/line fitting.
4. Return candidates with source and confidence.
5. Inspector confirms candidates before evaluation.
6. Final evaluation uses calibrated geometry, not AI confidence alone.

P1 implementation uses OpenCV only; no AI model inference is required for line, angle, or hole geometry. AI-assisted semantic selection remains a later optional phase after deterministic accuracy is validated.

`REVIEW` reasons include `invalid_calibration`, `unsupported_view`, `no_usable_candidate`, `ambiguous_candidate`, `low_confidence`, and `missing_nominal_or_tolerance`.

## Acceptance criteria

- A reference line drawn on the image computes `reference_px` and `mm_per_pixel` without a manually typed pixel value.
- `linear_dimension` retains existing prototype behavior.
- Hole processing returns center/radius candidates for a synthetic clean circle.
- Hole diameter uses the refined radius, not blindly `2 * Hough radius`.
- Center-to-center and edge-to-edge calculations are deterministic.
- A top-down `thickness_profile` or `bend_angle` task returns `REVIEW`, not `PASS`.
- Existing image/Live Camera/Mobile Camera, History, Audit, and linear tests remain green.
