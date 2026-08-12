# Inspect Measurement Proper - Milestone Tracker

**PRD:** [`inspect-measurement-proper.md`](./inspect-measurement-proper.md)
**Specification:** [`inspect-measurement-proper-spec.md`](./inspect-measurement-proper-spec.md)
**Status:** P1-P2 software slice done; P2.1 geometry refinement approved; physical accuracy and P3-P6 planned
**Last updated:** 12 August 2026

| Milestone | Status | Exit checkpoint |
|---|---|---|
| P0 - Proper scope and OpenCV baseline | DONE | Task types, pose constraints, hole geometry, station calibration shape, and OpenCV 4.13 baseline documented. |
| P1 - Planar calibration and task contract | DONE | Reference-line calibration, task/view metadata, station-profile shape, and backwards-compatible process response. |
| P2 - Session and multi-view Studio slice | DONE (software) | Dynamic Image/Live/Mobile views, Global/Detail profile CRUD, pose/capability gate, save/reopen/delete, completion guard, History, and Audit pass focused checks. Physical station accuracy remains open. |
| P2.1 - Logical planar geometry | PLANNED | Dual-axis calibration, logical edges, outer span, corner radius, bend angle, and inspector-friendly layers pass focused checks. |
| P3 - Drawing recipe and source of truth | PLANNED | Measured feature compares against approved drawing/recipe revision. |
| P4 - Profile measurement | PLANNED | Thickness, bend, and inclination validated on approved profile station. |
| P5 - AI-assisted selection | PLANNED | Semantic edge/feature assistance improves review without replacing deterministic geometry. |
| P6 - Accuracy gate | PLANNED | Repeatability/reproducibility evidence enables selected tasks as quality gates. |

## Checkpoint detail

| Area | Status | Evidence |
|---|---|---|
| OpenCV planar candidate kernel | DONE | LSD-first lines, Hough fallback, circle candidates, contour/ellipse refinement, deterministic geometry tests. |
| Logical geometry refinement | PLANNED | Approved design covers collinear grouping, robust line fit, outer contour span, selected arc radius, and selected flange angle. |
| Manual calibration | DONE | Reference-line calibration with `mm_per_pixel`, invalid-calibration `REVIEW` gate. |
| Task contract | DONE | Linear, inclination, bend/profile, hole diameter, pitch, edge distance, center-to-edge. |
| Measurement session | DONE | `MeasurementSession` parent, dynamic views, manual naming, selected-view process, save/reopen/delete, completion guard. |
| Measurement profile | DONE (software) | `GLOBAL` / `DETAIL` CRUD, resolution/camera binding, calibration status, capability min/max checks. |
| QC Station accuracy | PLANNED | C50 development evidence, fixed height/FOV, reference artifact, repeatability, and drift limits. |
| Drawing source of truth | PLANNED | PDF/CAD recipe mapping, revision, datum, feature ID, and approval workflow. |

## Verification log

| Date | Checkpoint | Evidence | Result |
|---|---|---|---|
| 2026-08-10 | Proper scope and OpenCV baseline | PRD, spec, Context7-verified OpenCV API baseline | Planar task types, hole pipeline, and profile boundary agreed. |
| 2026-08-10 | P1-P3 planar vertical slice | Backend/frontend tests, build, Measurement Studio Playwright | Drawn calibration, task/view contracts, LSD/Hough lines, hole geometry, bend/inclination UI, History, and Audit verified. |
| 2026-08-10 | Camera staging calibration correction | Backend/frontend tests, build, staged Live Camera E2E | Live and Mobile Camera stage frames before explicit Process Measurement. |
| 2026-08-11 | Multi-view station software slice | Commits `edb2cfd`, `573a745`, `784f218`, `c728f0b`, `995017f`, `663f018`; focused backend/frontend tests and Measurement Studio E2E | Session/profile persistence, Global/Detail capability rules, dynamic view queue, pose guidance, selected-view processing, save/reopen/delete, completion guard, History, and Audit implemented. No production accuracy claim. |
| 2026-08-12 | P2.1 2D geometry design | `inspect-measurement-2d-geometry-improvement-design.md` | Design approved; implementation and physical accuracy evidence remain pending. |

## Accuracy gate checklist

- [ ] Known-scale planar sample tested across image positions.
- [ ] Rotated/repositioned component tested.
- [ ] Glare/noise sample tested.
- [ ] Invalid calibration returns `REVIEW`.
- [ ] Absolute error and repeatability recorded.
- [ ] No production claim for `+/-2 mm` or `+/-0.5 deg` without station evidence.
