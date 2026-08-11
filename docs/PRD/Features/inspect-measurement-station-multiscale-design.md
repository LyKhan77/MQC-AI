# Inspect Measurement Station and Multi-View Design

**Status:** Approved design; implementation plan pending review  
**Date:** 11 August 2026  
**Parent PRD:** [`inspect-measurement-proper.md`](./inspect-measurement-proper.md)  
**Related specification:** [`inspect-measurement-proper-spec.md`](./inspect-measurement-proper-spec.md)

## Goal

Support one component inspection session with multiple staged inputs and multiple physical views while keeping the camera fixed top-down. The inspector changes the component pose; the system selects the correct measurement scale, calibration profile, task guidance, and evidence record.

## Decisions

### Camera and optical scale

- Production station uses two fixed top-down camera profiles:
  - `GLOBAL`: complete component envelope, up to approximately 2100 mm.
  - `DETAIL`: small features and dimensions down to approximately 1 mm.
- A single global FOV must not be used to measure both 2100 mm span and 1 mm feature. At 2560 pixels across 2100 mm, sampling is approximately 0.82 mm/pixel and cannot provide reliable 1 mm measurement.
- Development may use one Fantech Luminous C50 at two repeatable calibrated positions to simulate `GLOBAL` and `DETAIL`. This validates workflow and geometry only, not production accuracy.
- Every scale has its own calibration revision, supported feature range, and quality gate.

### Camera pose and component pose

- Camera angle remains top-down and station mounting remains fixed.
- Rotating the component horizontally on the desk (`yaw`) changes orientation but not measurement plane; it still measures the currently upward-facing face.
- Measuring another face requires flipping or repositioning the component so that target face is upward and flat on the calibrated desk plane.
- A component that is lifted or freely tilted is not a valid calibrated pose. The result becomes `REVIEW` unless a profile fixture/calibration explicitly supports it.
- Thickness/profile measurement requires a stable `PROFILE_FACE` pose. It cannot be inferred from a normal flat top view.

### Dynamic views and sources

- One session has no fixed view count.
- Image upload, Live Camera, Mobile Camera, and Server Camera all create the same staged `InspectionView` shape.
- Capture never runs LSD or measurement automatically. It only creates a staged frame.
- Processing is explicit and applies only to the selected staged view.
- Each view is independently processed, evaluated, saved, and revisited.

## Inspector workflow

```text
Create session
  -> Manual component/series name
  -> Add one or more inputs
  -> Select staged image
  -> Choose view label and pose
  -> Choose measurement task
  -> Select/validate camera scale profile
  -> Draw reference line when station calibration is unavailable
  -> Process Measurement
  -> Confirm or correct geometry
  -> Evaluate tolerance
  -> Save view result
  -> Rotate/reposition component
  -> Capture next view
  -> Complete session
```

Plain-language pose guidance:

- `TOP_FACE`: Place top face flat.
- `REVERSE_FACE`: Flip component; place reverse face flat.
- `PROFILE_FACE`: Place profile/side face flat using the station support.
- `CUSTOM_FACE`: Inspector labels the custom face manually.

The system does not assume that `front`, `back`, `left`, or `right` can be inferred from pixels. View labels come from the inspector or an approved drawing recipe.

## Measurement capability routing

| Task | Recommended pose | Scale | Result rule |
|---|---|---|---|
| Length/width up to 2100 mm | `TOP_FACE` or `REVERSE_FACE` | `GLOBAL` | Measure if full edge geometry is visible. |
| Small planar edge around 1 mm | Face containing edge flat | `DETAIL` | Reject/`REVIEW` if feature is below profile capability. |
| Hole diameter/pitch | Face containing holes flat | `GLOBAL` or `DETAIL` | Select scale from hole size and tolerance. |
| Edge/hole distance | Same face as edge and hole | `GLOBAL` or `DETAIL` | Both geometry references must be in calibrated plane. |
| Thickness/profile width | `PROFILE_FACE` | `DETAIL` | Never `PASS` from ordinary top view. |
| Bend angle | `PROFILE_FACE` or approved multi-view pose | `DETAIL`/profile | Requires validated profile plane or fixture. |
| 2D inclination | Current calibrated face | `GLOBAL` or `DETAIL` | Compare against explicit datum axis. |

Drawing recipes can map each feature to `pose_type`, `scale_profile`, nominal, tolerance, datum, and expected view. Manual recipe mapping remains authority until PDF/CAD extraction has human approval.

## Station profile contract

Each profile stores:

```text
profile_id
station_id
camera_id
camera_serial (when available)
resolution
working_distance_nominal
fov_nominal
measurement_plane
calibration_revision
camera_matrix
distortion_coefficients
homography
mm_per_pixel / scale model
minimum_supported_feature_mm
maximum_supported_span_mm
validation_status
validated_at
```

The runtime must bind calibration to actual camera identity and input resolution. A resolution mismatch, invalid calibration, missing marker, failed quality check, or unsupported feature size produces `REVIEW` or blocks processing.

## Staged view contract

```json
{
  "id": "view-01",
  "session_id": "session-01",
  "source_type": "live_camera",
  "source_key": "tmp-...",
  "view_label": "top face",
  "pose_type": "TOP_FACE",
  "task_type": "linear_dimension",
  "scale_profile": "GLOBAL",
  "calibration_revision": "cal-...",
  "status": "captured"
}
```

View status:

```text
CAPTURED -> ASSIGNED -> CALIBRATED -> PROCESSED -> EVALUATED -> SAVED
```

The session stores original frames, processed overlays, selected geometry, task metadata, tolerance evaluation, source metadata, calibration revision, and audit events.

## Overlay requirements

Before processing, the canvas displays:

- active `GLOBAL` or `DETAIL` profile;
- actual image resolution;
- calibration status and revision;
- work-area boundary;
- mm grid/rulers when calibration is valid;
- safe placement margin;
- task/pose instruction;
- unsupported-scale warning;
- blur, glare, out-of-area, and marker warnings.

The overlay must not show LSD candidates before `Process Measurement`. After processing, candidate geometry becomes visible and remains editable/auditable.

## Accuracy policy

- The C50 is a development camera for workflow and algorithm validation.
- Production quality-gate capability requires reference-artifact testing for every scale profile.
- Accuracy is recorded per profile and task, not declared globally.
- A default tolerance is not an accuracy guarantee.
- The system must report `REVIEW` when optical sampling, pose, calibration, or geometry confidence cannot support the requested task.

## Implementation boundary

First implementation targets:

1. Capability matrix and scale-profile contract.
2. Multi-input staging within one session.
3. View/pose/task assignment before processing.
4. Global/detail calibration and overlay status.
5. Per-view process/evaluate/save flow.
6. History and Audit session evidence.

Deferred:

- Production industrial camera integration.
- Automatic PDF/CAD feature extraction.
- True 3D bend measurement.
- Thickness measurement without a validated profile fixture.
- Automatic semantic identification of front/back/left/right faces.

## Acceptance criteria

- One session can contain any number of Image, Live, Mobile, and Server Camera views.
- Capture stages a frame without running measurement.
- Inspector selects view label, pose, task, and scale before processing.
- Global profile cannot process a feature below its capability range.
- Detail profile can process small planar features after calibration validation.
- Thickness task from `TOP_FACE` returns `REVIEW`, not `PASS`.
- Profile thickness requires `PROFILE_FACE` and a valid calibrated pose.
- Each saved view keeps source, calibration, task, geometry, evaluation, and audit evidence.
