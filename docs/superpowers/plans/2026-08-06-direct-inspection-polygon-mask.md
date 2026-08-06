# Direct Inspection Polygon Mask Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add staged upload processing with one editable polygon ROI per image, server-side masked SAM3 inference, full-image remapped results, and persisted mask overlays in QC Studio.

**Architecture:** Keep mobile/server-camera Direct Inspection behavior unchanged. Upload mode becomes a staging workflow owned by `DirectInspection.vue`; `MaskEditor.vue` emits image-coordinate polygons. The backend validates each polygon, extracts a bounded ROI, runs the existing defect strategy on that ROI, translates defect polygons back to full-image coordinates, and persists `mask_polygon` on `Image`.

**Tech Stack:** Vue 3 Composition API, SVG pointer overlay, FastAPI, OpenCV, SQLAlchemy 2.0, Pydantic v2, SQLite JSON column, Vitest, pytest, Playwright.

## Global Constraints

- One polygon per image; multiple polygons and brush masks are out of scope.
- Upload files stage without invoking `/api/inspection/detect` until `Process QC` is pressed.
- Images without polygons process full-frame, even while Masking is enabled.
- Masking takes priority over Auto-crop; Auto-crop is disabled for masked upload processing.
- Results remain full images with defect coordinates mapped to original image coordinates.
- Mask polygon persists through Direct Inspection, `POST /api/inspection/to-qc`, batch `ImageOut`, `result.json`, and QC Studio.
- Mobile-camera and server-camera flows remain unchanged.
- Use existing defect color resolver and existing image-coordinate conventions; no UI library or new dependency.
- Add user-facing copy to both `qc_frontend/src/assets/locales/id.js` and `qc_frontend/src/assets/locales/en.js`.

---

## Task 1: Add and test polygon ROI primitives

**Files:**
- Create: `qc_server/app/services/polygon_mask.py`
- Create: `qc_server/tests/test_polygon_mask.py`

**Interfaces:**
- Produces `validate_polygon(points, width, height) -> list[list[int]]`.
- Produces `prepare_polygon_roi(frame, polygon) -> tuple[numpy.ndarray, tuple[int, int]]`.
- Produces `remap_polygon(polygon, offset_x, offset_y) -> list[list[int]]`.
- Produces `polygon_has_overlap(candidate, mask) -> bool` for post-inference filtering.

- [ ] **Step 1: Write failing tests for validation and coordinate math**

```python
def test_validate_polygon_rejects_fewer_than_three_points():
    with pytest.raises(ValueError, match="at least three"):
        validate_polygon([[1, 1], [5, 1]], 20, 20)


def test_validate_polygon_rejects_out_of_bounds_points():
    with pytest.raises(ValueError, match="bounds"):
        validate_polygon([[1, 1], [19, 1], [21, 10]], 20, 20)


def test_prepare_roi_returns_bbox_offset_and_masked_pixels():
    frame = np.full((40, 50, 3), 255, dtype=np.uint8)
    roi, offset = prepare_polygon_roi(frame, [[10, 10], [30, 10], [30, 30], [10, 30]])
    assert offset == (10, 10)
    assert roi.shape[:2] == (20, 20)


def test_remap_polygon_restores_original_coordinates():
    assert remap_polygon([[0, 0], [20, 0], [20, 20]], 10, 12) == [[10, 12], [30, 12], [30, 32]]
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `qc_server/.venv/Scripts/python.exe -m pytest -q qc_server/tests/test_polygon_mask.py`

Expected: FAIL because `polygon_mask.py` and its functions do not exist.

- [ ] **Step 3: Implement the minimal OpenCV helper**

Use `cv2.fillPoly` on a local ROI mask. Clamp integer coordinates only after validating finite numeric input. Return the tight bounding rectangle offset so callers can translate inference polygons without changing the SAM strategy interface.

- [ ] **Step 4: Run focused tests**

Run: `qc_server/.venv/Scripts/python.exe -m pytest -q qc_server/tests/test_polygon_mask.py`

Expected: all focused tests pass.

- [ ] **Step 5: Commit**

```bash
git add qc_server/app/services/polygon_mask.py qc_server/tests/test_polygon_mask.py
git commit -m "feat: add polygon ROI helpers"
```

## Task 2: Persist mask polygons in image records and results

**Files:**
- Modify: `qc_server/app/models.py:Image`
- Modify: `qc_server/app/schemas.py:ImageOut`
- Modify: `qc_server/app/database.py` or startup migration call site
- Modify: `qc_server/app/main.py:on_startup`
- Modify: `qc_server/app/storage.py:write_result_json`
- Test: `qc_server/tests/test_migration.py`
- Test: `qc_server/tests/test_batches.py`

**Interfaces:**
- `Image.mask_polygon: list | None` is nullable JSON storage.
- `ImageOut.mask_polygon: list | None` serializes the stored polygon.

- [ ] **Step 1: Add failing persistence tests**

Create an image with `mask_polygon=[[10, 10], [30, 10], [20, 30]]`, fetch its batch result, and assert the field is returned. Add a startup migration test that creates an old `images` table and verifies the additive column appears after startup migration.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `qc_server/.venv/Scripts/python.exe -m pytest -q qc_server/tests/test_migration.py qc_server/tests/test_batches.py`

Expected: FAIL because the ORM/schema/result do not expose `mask_polygon`.

- [ ] **Step 3: Add nullable JSON field and guarded migration**

Add:

```python
mask_polygon: Mapped[list | None] = mapped_column(JSON, nullable=True, default=None)
```

Call `ensure_column(engine, "images", "mask_polygon", "JSON")` during startup after `Base.metadata.create_all(engine)`. Add the field to `ImageOut` and `write_result_json`.

- [ ] **Step 4: Run focused tests**

Run: `qc_server/.venv/Scripts/python.exe -m pytest -q qc_server/tests/test_migration.py qc_server/tests/test_batches.py`

Expected: all focused tests pass.

- [ ] **Step 5: Commit**

```bash
git add qc_server/app/models.py qc_server/app/schemas.py qc_server/app/database.py qc_server/app/main.py qc_server/app/storage.py qc_server/tests/test_migration.py qc_server/tests/test_batches.py
git commit -m "feat: persist Direct Inspection mask polygons"
```

## Task 3: Add masked Direct Inspection inference and coordinate remapping

**Files:**
- Modify: `qc_server/app/routers/inspection.py:detect_inspection,_detect_frame,inspection_to_qc`
- Modify: `qc_server/tests/test_inspection.py`

**Interfaces:**
- `POST /api/inspection/detect` accepts multipart `mask_polygon` JSON.
- Detect response adds `mask_polygon: list | None`, `mask_applied: bool`, and original `width`/`height`.
- `POST /api/inspection/to-qc` accepts `mask_polygon` per capture item.

- [ ] **Step 1: Add failing endpoint tests**

Add tests for:

```python
def test_detect_rejects_invalid_mask_polygon(client):
    response = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={"mask_polygon": json.dumps([[1, 1], [2, 2]])},
    )
    assert response.status_code == 400


def test_detect_mask_returns_full_image_coordinates(client, monkeypatch):
    class RoiStrategy:
        def detect(self, image_path, width, height, defect_classes, params):
            assert (width, height) == (20, 20)
            return [Detection("scratch", "coating", 0.9, [[1, 1], [4, 1], [4, 4]])]

    monkeypatch.setattr(inspection, "get_strategy", lambda _: RoiStrategy())
    response = client.post(
        "/api/inspection/detect",
        files={"file": ("part.png", io.BytesIO(_png_bytes()), "image/png")},
        data={
            "crop_mode": "auto",
            "mask_polygon": json.dumps([[10, 10], [30, 10], [30, 30], [10, 30]]),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mask_applied"] is True
    assert body["width"] == 40 and body["height"] == 40
    assert body["defects"][0]["polygon"] == [[11, 11], [14, 11], [14, 14]]
```

The test fixture must use a deterministic strategy stub; it must not load SAM3 weights.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `qc_server/.venv/Scripts/python.exe -m pytest -q qc_server/tests/test_inspection.py`

Expected: FAIL because `mask_polygon` is not parsed or applied.

- [ ] **Step 3: Parse and validate request polygon**

Add `mask_polygon: str | None = Form(default=None)`. Parse JSON only when present. Call `validate_polygon` with decoded frame dimensions. Return HTTP 400 with the validation message for malformed JSON or invalid geometry.

- [ ] **Step 4: Run ROI inference without changing strategy signatures**

For a valid mask:

```python
roi, (offset_x, offset_y) = prepare_polygon_roi(original, polygon)
result = _detect_frame(
    inference_frame=roi,
    output_frame=original,
    setting=setting,
    db=db,
    coordinate_offset=(offset_x, offset_y),
    mask_polygon=polygon,
)
```

Update `_detect_frame` so it saves `output_frame` as `frame.jpg`, saves a temporary ROI inference image separately, invokes the existing strategy with ROI dimensions, remaps each returned defect polygon using `remap_polygon`, filters candidates without meaningful overlap, and returns original image dimensions. Keep the existing full-frame path unchanged when `mask_polygon` is absent.

- [ ] **Step 5: Handle Auto-crop priority and handoff metadata**

When `mask_polygon` is present, skip `analyze_autocrop`, report masking as active, and include the normalized polygon in the response. In `inspection_to_qc`, assign each capture polygon to its matching `Image.mask_polygon` after `prepare_images` creates image rows, then call `write_result_json`.

- [ ] **Step 6: Run focused tests**

Run: `qc_server/.venv/Scripts/python.exe -m pytest -q qc_server/tests/test_inspection.py qc_server/tests/test_batches.py`

Expected: all masked inference, full-frame fallback, Auto-crop bypass, and persistence tests pass.

- [ ] **Step 7: Commit**

```bash
git add qc_server/app/routers/inspection.py qc_server/tests/test_inspection.py
git commit -m "feat: process Direct Inspection polygon ROIs"
```

## Task 4: Build reusable polygon mask editor

**Files:**
- Create: `qc_frontend/src/components/MaskEditor.vue`
- Modify: `qc_frontend/src/utils/canvasCoords.js` only if a shared polygon helper is required
- Create: `qc_frontend/src/components/__tests__/MaskEditor.test.js`

**Interfaces:**
- Props: `src`, `width`, `height`, `modelValue`, `disabled`.
- Emits: `update:modelValue`, `finish`, `clear`.
- Polygon points are always integer image coordinates: `number[][]`.

- [ ] **Step 1: Write failing component tests**

Mount with a 100×80 image and verify:

```js
await wrapper.find('[data-testid="mask-canvas"]').trigger('click', { clientX: 10, clientY: 10 })
expect(wrapper.emitted('update:modelValue')[0][0]).toEqual([[10, 10]])
```

Add tests for three-point Finish, double-click Finish, Undo, Clear, and disabled input.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `npm test -- --run src/components/__tests__/MaskEditor.test.js`

Expected: FAIL because `MaskEditor.vue` does not exist.

- [ ] **Step 3: Implement image-coordinate SVG editor**

Use `toImageCoords(clientX, clientY, svg.getBoundingClientRect(), width, height)`. Render the image, in-progress polyline, closed polygon, and vertex handles in one SVG `viewBox`. Expose `data-testid="mask-canvas"`, `data-testid="mask-finish"`, `data-testid="mask-undo"`, and `data-testid="mask-clear"` for tests and Playwright.

- [ ] **Step 4: Run focused tests**

Run: `npm test -- --run src/components/__tests__/MaskEditor.test.js`

Expected: all editor tests pass.

- [ ] **Step 5: Commit**

```bash
git add qc_frontend/src/components/MaskEditor.vue qc_frontend/src/components/__tests__/MaskEditor.test.js qc_frontend/src/utils/canvasCoords.js
git commit -m "feat: add Direct Inspection polygon mask editor"
```

## Task 5: Convert upload Direct Inspection to staging and trigger processing

**Files:**
- Modify: `qc_frontend/src/api/inspection.js:detectInspection`
- Modify: `qc_frontend/src/views/DirectInspection.vue`
- Modify: `qc_frontend/src/views/__tests__/DirectInspection.test.js`
- Modify: `qc_frontend/src/assets/locales/id.js`
- Modify: `qc_frontend/src/assets/locales/en.js`

**Interfaces:**
- `detectInspection({ file, cameraId, cropMode, debugCrop, maskPolygon })` sends `mask_polygon` only when polygon is non-null.
- Staged item shape: `{ id, file, previewUrl, width, height, maskPolygon, maskStatus, status, error }`.

- [ ] **Step 1: Add failing upload staging tests**

Verify upload changes only staged state:

```js
await input.trigger('change')
expect(mocks.detectInspection).not.toHaveBeenCalled()
expect(wrapper.findAll('.mask-stage-item')).toHaveLength(2)
```

Add tests that Process QC sends one request per staged image, includes polygon for masked image, omits polygon for unmasked image, and leaves mobile/server capture tests working.

- [ ] **Step 2: Run focused tests and verify failure**

Run: `npm test -- --run src/views/__tests__/DirectInspection.test.js`

Expected: FAIL because upload currently invokes `pushDetect` immediately.

- [ ] **Step 3: Add API mask payload**

Append the normalized polygon JSON:

```js
if (maskPolygon?.length) fd.append('mask_polygon', JSON.stringify(maskPolygon))
```

- [ ] **Step 4: Add staging state and upload UI**

Replace upload `onFiles` processing with stage creation and preview URL cleanup. Add `Masking` toggle, per-image `MaskEditor`, explicit `Process QC`, full-frame label for images without polygons, per-image status/error, and remove/clear controls. Keep `pushDetect` for mobile/server captures.

When Masking is enabled, disable the upload Auto-crop choice and send `cropMode: 'full'` for staged upload processing. When disabled, preserve current crop selection.

- [ ] **Step 5: Implement sequential trigger and result mapping**

Process staged items sequentially to avoid simultaneous SAM3 memory spikes. Add each successful response to the existing result stack with `mask_polygon`; keep failed staged items visible for retry. Disable Send to QC while any staged item is processing.

- [ ] **Step 6: Add bilingual copy and overlay**

Add translations for `Masking`, `Process QC`, `Finish`, `Undo`, `Clear`, `Full frame`, mask validation, staging status, and processing errors. Render mask polygon on the full-image result with a labeled overlay; use existing defect colors for defects.

- [ ] **Step 7: Run focused tests**

Run: `npm test -- --run src/views/__tests__/DirectInspection.test.js`

Expected: existing Direct Inspection tests plus staging/masking tests pass.

- [ ] **Step 8: Commit**

```bash
git add qc_frontend/src/api/inspection.js qc_frontend/src/views/DirectInspection.vue qc_frontend/src/views/__tests__/DirectInspection.test.js qc_frontend/src/assets/locales/id.js qc_frontend/src/assets/locales/en.js
git commit -m "feat: stage Direct Inspection uploads before QC"
```

## Task 6: Display persisted masks in QC Studio

**Files:**
- Modify: `qc_frontend/src/components/InspectionCanvas.vue`
- Modify: `qc_frontend/src/components/__tests__/InspectionCanvas.test.js`

**Interfaces:**
- Consumes `selected.mask_polygon` from the existing `useInspection().selected` image.
- Produces a non-editable mask layer rendered in image coordinates.

- [ ] **Step 1: Add failing render test**

Mount an image with `mask_polygon` and assert the canvas contains a polygon mask element with the expected points. Mount an image without a mask and assert no mask element renders.

- [ ] **Step 2: Run focused test and verify failure**

Run: `npm test -- --run src/components/__tests__/InspectionCanvas.test.js`

Expected: FAIL because QC Studio does not render `mask_polygon`.

- [ ] **Step 3: Add labeled non-editable mask layer**

Render the mask polygon behind defect polygons, use a blue translucent fill/outline, and add a text label or legend entry `Processing mask`. Do not include the mask in defect selection, reshape handles, delete actions, or defect exports.

- [ ] **Step 4: Run focused test**

Run: `npm test -- --run src/components/__tests__/InspectionCanvas.test.js`

Expected: pass with existing edit-mode behavior unchanged.

- [ ] **Step 5: Commit**

```bash
git add qc_frontend/src/components/InspectionCanvas.vue qc_frontend/src/components/__tests__/InspectionCanvas.test.js
git commit -m "feat: show processing masks in QC Studio"
```

## Task 7: Add browser flow coverage and update project docs

**Files:**
- Create: `qc_frontend/tests/e2e/direct-inspection-mask.e2e.js`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add Playwright mocked upload flow**

Mock `/api/inspection/detect` and `/api/inspection/to-qc`. Upload two files, draw/finish a polygon on one staged image, leave the other unmasked, click `Process QC`, and assert the requests contain one `mask_polygon` and one full-frame request. Assert mask/result overlays are visible.

- [ ] **Step 2: Run browser test and verify**

Run: `npm run test:e2e -- --reporter=line`

Expected: existing settings/reports tests and the polygon-mask flow pass.

- [ ] **Step 3: Update living documentation**

Document upload staging, per-image polygon mask, full-frame fallback, ROI remapping, persistence, and QC Studio display in the current feature/state sections. Add a dated CHANGELOG entry with tests.

- [ ] **Step 4: Commit**

```bash
git add qc_frontend/tests/e2e/direct-inspection-mask.e2e.js README.md AGENTS.md CHANGELOG.md
git commit -m "docs: record Direct Inspection polygon masking"
```

## Task 8: Run merged feature verification

**Files:**
- No source changes expected.

- [ ] **Step 1: Run frontend unit tests**

Run: `npm test -- --run`

Expected: all frontend tests pass.

- [ ] **Step 2: Run backend tests**

Run from repository root: `qc_server/.venv/Scripts/python.exe -m pytest -q`

Expected: all backend tests pass; existing deprecation warnings are acceptable.

- [ ] **Step 3: Run production build and Playwright**

Run: `npm run build` and `npm run test:e2e -- --reporter=line` from `qc_frontend`.

Expected: build succeeds and all browser tests pass.

- [ ] **Step 4: Check repository state**

Run: `git diff --check; git status --short --branch`

Expected: no whitespace errors and only intentional commits on `feature/direct-inspection-polygon-mask`.

- [ ] **Step 5: Commit only if verification documentation changed**

No empty commit. If verification requires a documentation correction, commit that correction with a descriptive message and rerun the affected check.
