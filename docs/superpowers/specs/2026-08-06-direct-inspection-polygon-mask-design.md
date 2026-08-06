# Direct Inspection Polygon Mask Design

**Status:** Draft for user review  
**Branch:** `feature/direct-inspection-polygon-mask`  
**Date:** 2026-08-06

## Problem

Direct Inspection currently sends uploaded images to QC processing immediately. Operators cannot restrict SAM3 processing to a selected part of an image, which can produce unwanted detections from fixtures, background, or adjacent objects.

## Goals

- Stage uploaded images without running segmentation.
- Let an operator enable masking and draw one precise polygon per staged image.
- Process all staged images with one explicit trigger.
- Use the polygon as the processing ROI while preserving full-image output and coordinates.
- Process images without a polygon as full-frame when masking is enabled.
- Persist the polygon so QC Studio and audit data retain operator intent.
- Keep existing mobile-camera and server-camera flows unchanged.

## Non-goals

- Multiple polygons per image.
- Freehand brush masks.
- Masking mobile or server-camera captures in this slice.
- Running Auto-crop together with polygon masking.
- Changing SAM3 prompt, confidence, or defect-class configuration.

## Operator flow

1. Operator opens Direct Inspection and selects `Upload`.
2. Operator selects one or more images. Files enter a staging list; no QC request is sent.
3. Operator enables `Masking` when ROI processing is needed.
4. Each staged image exposes a polygon editor. Operator clicks vertices, then chooses `Finish` or double-clicks the last vertex.
5. Editor supports `Undo`, `Clear`, and `Edit` before processing. Polygon requires at least three vertices.
6. Images without a polygon remain valid and are marked `Full frame`.
7. Operator presses `Process QC`.
8. Backend processes each image sequentially with its polygon, or full-frame when polygon is absent.
9. Results appear as full images. Masked images show the saved ROI outline plus defect overlays; defect coordinates remain in the original image coordinate system.
10. Operator can remove captures and send approved results to QC Studio as today.

When masking is enabled, Auto-crop is disabled for uploaded images. When masking is disabled, the existing full-frame/Auto-crop selection remains available at Process time.

## UX state

Each staged image owns:

```text
file
preview URL
width / height
mask polygon or null
mask status: none | editing | ready
processing status: staged | processing | done | error
error message, if any
```

The trigger remains enabled when every staged image is either `mask ready` or `none`. The UI clearly labels images without masks as `Full frame`; no silent behavior is allowed.

The polygon overlay uses a restrained blue fill and outline. Defect polygons continue using the configured `DefectClass.color` resolver. The full-image result shows both layers with a legend or text labels so status does not rely on color alone.

## Frontend changes

### Direct Inspection

- Replace immediate upload processing with staging for upload sources.
- Add a `Masking` toggle and `Process QC` trigger in the upload panel.
- Add one polygon editor per staged image using image-coordinate mapping, not CSS-pixel coordinates.
- Reuse existing canvas coordinate and inspection overlay conventions.
- Preserve current result stack, remove action, defect preview, and Send to QC Studio handoff.
- Keep mobile and server-camera capture actions on the current immediate-capture flow.

### API client

`detectInspection` gains optional `maskPolygon`. The client sends it as JSON in the multipart `mask_polygon` field. The client also sends the selected `cropMode`; the backend treats a non-null mask as higher priority than Auto-crop.

## Backend changes

### Detect request

`POST /api/inspection/detect` accepts optional `mask_polygon` JSON form data.

Validation:

- JSON must be an array of at least three `[x, y]` points.
- Coordinates must be finite and inside the decoded image bounds.
- Invalid polygon returns HTTP `400` with a clear message.
- Missing polygon means full-frame processing.
- A polygon with fewer than three valid points is not accepted.

### ROI inference

1. Decode and retain the original full-resolution frame.
2. If a mask exists, calculate its bounding rectangle.
3. Extract the bounding-rectangle ROI and apply the polygon mask in ROI coordinates.
4. Run the configured defect strategy on that ROI only.
5. Translate every returned defect polygon from ROI coordinates back to original image coordinates.
6. Discard detections whose polygon has no meaningful overlap with the requested mask.
7. Save and return the original full frame as `frame.jpg`; return original `width` and `height`.
8. Return `mask_polygon`, `mask_applied`, and existing defect/capture fields.

Masking avoids artificial full-frame black borders by limiting inference to the polygon bounding rectangle. The polygon remains the authoritative filter boundary after inference.

When `mask_polygon` exists, `crop_mode=auto` is ignored for inference and the response reports masking as the active crop mode. This prevents double-cropping and ambiguous coordinates.

### Capture handoff and persistence

`POST /api/inspection/to-qc` accepts `mask_polygon` in each capture item. The image record gains nullable `mask_polygon` JSON storage. Existing databases receive a guarded additive migration at startup.

`ImageOut` and `result.json` include `mask_polygon` when present. QC Studio renders the mask outline behind/alongside defect polygons without changing defect editing behavior.

## Error handling

- Empty staging list: `Process QC` disabled.
- Invalid image: stage item marked `error`; other items remain available.
- Invalid polygon: editor remains active and displays validation text.
- Missing QC model: existing HTTP `409` behavior remains.
- One image failure: failed item shows error; successful items remain reviewable. Trigger can retry failed items without duplicating successful results.
- Send to QC Studio remains unavailable while any item is still processing.

## Testing

### Backend

- Accept valid polygon and return `mask_polygon` plus `mask_applied`.
- Reject fewer than three points, non-finite points, and out-of-bounds points.
- Verify strategy receives ROI dimensions rather than full-frame dimensions.
- Verify defect coordinates are translated back to full-image coordinates.
- Verify full-frame fallback when mask is absent.
- Verify Auto-crop is bypassed when mask exists.
- Verify mask persists through `to-qc`, batch result, and `ImageOut`.

### Frontend

- Upload does not call detect before `Process QC`.
- Multiple files create independent staging cards.
- Polygon draw, finish, undo, clear, and edit update only the selected image.
- Masked and unmasked images process in one trigger with correct request payloads.
- Full-frame fallback label appears for an image without a mask.
- Result renders full image with mask and defect overlays.
- Existing mobile/server-camera flow remains covered.

### Playwright

- Upload mocked images, draw a polygon, finish it, trigger Process QC, and verify request payload.
- Verify unmasked staged image sends no polygon and remains full-frame.
- Verify mask overlay and result status are visible.

## Acceptance criteria

- Uploading files alone never invokes SAM3 or `/api/inspection/detect`.
- One trigger processes all staged images.
- Polygon-masked processing produces defects only from the selected ROI and returns full-image coordinates.
- Unmasked images process full-frame even while Masking is enabled.
- Mask polygon is visible in Direct Inspection results and persists into QC Studio.
- Existing report, mobile-camera, server-camera, and Send to QC Studio workflows remain functional.
- Frontend unit tests, backend tests, production build, and Playwright pass.
