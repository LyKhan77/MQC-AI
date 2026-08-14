# Inspect Measurement Stage 00 Software Improvement Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Maksimalkan robustness edge detector dan calibration jig pada Stage 00 (webcam + HVS), tanpa klaim presisi production dan tanpa threshold CV manual untuk inspector.

**Architecture:** Download memakai staged file/blob URL yang sudah ada sehingga browser menyimpan raw image ke device client. Backend menghasilkan kandidat dari raw grayscale dan CLAHE; masing-masing variant menjalankan LSD serta Hough dengan Canny adaptif. Kandidat tetap memakai grouping/fit logical edge yang ada. Contour adalah fallback confidence rendah. Jig hanya menentukan garis X/Y; panjang fisik X/Y tetap manual.

**Tech Stack:** Vue 3, browser anchor download, FastAPI, OpenCV (`LSD_REFINE_ADV`, CLAHE, Canny, HoughLinesP, contour), pytest, Vitest.

**Spec:** [`inspect-measurement-prototype.md`](./inspect-measurement-prototype.md), [`inspect-measurement-prototype-milestones.md`](./inspect-measurement-prototype-milestones.md), [`inspect-measurement-development-station-setup.pdf`](../inspect-measurement-development-station-setup.pdf).

## Global Constraints

- Stage 00 proves software behavior only; physical accuracy and repeatability remain `PLANNED`.
- Top-down image only. Flash is not baseline lighting.
- Inspector never sets Canny/LSD/Hough threshold. Tuning is adaptive server logic and diagnostics are engineering-only.
- `PASS` rules do not change: independent calibration artifact, nominal, and tolerance remain mandatory.
- No dependency added.
- Add all UI strings to `qc_frontend/src/assets/locales/id.js` and `en.js`.

## File Map

| File | Responsibility |
|---|---|
| `qc_frontend/src/views/MeasurementStudio.vue` | Staged View download icon and collapsed diagnostics display. |
| `qc_frontend/src/views/__tests__/MeasurementStudio.test.js` | Download and diagnostics regression tests. |
| `qc_server/app/services/measurement.py` | Variant preprocessing, adaptive Canny, combined candidates, contour fallback, diagnostics. |
| `qc_server/app/routers/measurements.py` | Four-point jig geometry validation. |
| `qc_server/app/schemas.py` | Optional diagnostics response field if schema is explicit. |
| `qc_server/tests/test_measurement_cv.py` | Detector and contour unit tests. |
| `qc_server/tests/test_measurements.py` | API jig/diagnostics and raw fixture tests. |
| `docs/PRD/Features/inspect-measurement-prototype*.md` | I6 checkpoint and behavior record. |

## Acceptance Criteria

- Download icon writes raw original to browser client, never server directory, and has no overlay.
- Raw and CLAHE each run LSD and Hough. Hough is not contingent on empty LSD output.
- Canny values come from image intensity, not fixed `50/150`.
- Contour fallback is source-labelled, low-confidence, and cannot create PASS by itself.
- Auto-jig rejects four points that do not form a top-down rectangle; manual Draw X/Y stays available.
- Diagnostics report detector evidence without threshold controls in inspector UI.

---

### Task 1: Download raw original from Staged View

**Files:** Modify `qc_frontend/src/views/MeasurementStudio.vue`, `qc_frontend/src/views/__tests__/MeasurementStudio.test.js`, `qc_frontend/src/assets/locales/id.js`, `qc_frontend/src/assets/locales/en.js`.

**Interface:** `downloadStagedOriginal(view)` consumes `{ previewUrl, sourceFilename }` and triggers browser download.

- [x] **Step 1: Write failing test**

```js
it('downloads raw staged image without overlay', async () => {
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  const wrapper = mount(MeasurementStudio)
  await stage(wrapper, [file('top.jpg')])
  await wrapper.find('.view-card-download').trigger('click')
  expect(click).toHaveBeenCalled()
  click.mockRestore()
})
```

- [x] **Step 2: Verify RED**

Run `npm test -- --run src/views/__tests__/MeasurementStudio.test.js`.

Expected: FAIL because `.view-card-download` does not exist.

- [x] **Step 3: Implement minimum behavior**

```js
function downloadStagedOriginal(view) {
  if (!view?.previewUrl) return
  const anchor = document.createElement('a')
  anchor.href = view.previewUrl
  anchor.download = view.sourceFilename || 'measurement-capture.jpg'
  anchor.click()
}
```

Add an icon-only `.view-card-download` card button. Its handler uses `@click.stop`; `title` and `aria-label` use `t('measurement.downloadOriginal')`.

- [x] **Step 4: Verify GREEN and commit**

Run `npm test -- --run src/views/__tests__/MeasurementStudio.test.js`; expected PASS. Commit with `feat: download staged measurement originals`.

### Task 2: Adaptive preprocessing and combined line candidates

**Files:** Modify `qc_server/app/services/measurement.py`, `qc_server/tests/test_measurement_cv.py`.

**Interfaces:** Add `adaptive_canny(gray) -> tuple[np.ndarray, dict]`, `preprocess_variants(gray) -> dict[str, np.ndarray]`, and `line_candidates_from_variants(gray, min_length) -> tuple[list[dict], dict]`. `process_image()` preserves `candidates` and `logical_edges` response keys.

- [x] **Step 1: Write failing tests**

```python
def test_adaptive_canny_uses_frame_intensity_not_fixed_thresholds():
    _, dark = adaptive_canny(np.full((120, 160), 35, dtype=np.uint8))
    _, bright = adaptive_canny(np.full((120, 160), 220, dtype=np.uint8))
    assert dark["low"] != bright["low"]


def test_process_keeps_hough_candidates_when_lsd_has_candidates():
    result = process_image(_partial_edge_frame(), _calibration())
    assert any(item["source"].startswith("lsd_") for item in result["candidates"])
    assert any(item["source"].startswith("hough_") for item in result["candidates"])
```

- [x] **Step 2: Verify RED**

Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurement_cv.py -q`.

Expected: FAIL because helpers and always-on Hough do not exist.

- [x] **Step 3: Implement minimum behavior**

```python
def adaptive_canny(gray):
    median = float(np.median(gray))
    low = int(max(0, round(median * 0.66)))
    high = int(min(255, max(low + 20, round(median * 1.33))))
    return cv2.Canny(gray, low, high), {"low": low, "high": high, "median": round(median, 2)}


def preprocess_variants(gray):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    return {"raw": gray, "clahe": cv2.GaussianBlur(clahe, (3, 3), 0)}
```

Run `LSD_REFINE_ADV` and `HoughLinesP` for each variant. Source labels: `lsd_raw`, `lsd_clahe`, `hough_raw`, `hough_clahe`. Reuse existing `_line_candidate`, grouping, `cv2.fitLine`, and deduplication.

- [x] **Step 4: Verify GREEN and commit**

Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurement_cv.py -q`; expected PASS. Commit with `feat: combine adaptive line detector candidates`.

### Task 3: Contour fallback for missing boundary

**Files:** Modify `qc_server/app/services/measurement.py`, `qc_server/tests/test_measurement_cv.py`.

**Interface:** Add `contour_straight_candidates(contour, min_length) -> list[dict]`; every result has `source="contour_fallback"`, `confidence=0.45`, and `fallback=True`.

- [ ] **Step 1: Write failing test**

```python
def test_process_adds_low_confidence_contour_fallback_when_line_detection_misses_boundary(monkeypatch):
    monkeypatch.setattr(cv2, "createLineSegmentDetector", lambda *_: _no_line_detector())
    result = process_image(_rectangle_frame(), _calibration())
    fallback = [item for item in result["candidates"] if item["source"] == "contour_fallback"]
    assert fallback
    assert all(item["confidence"] <= 0.45 for item in fallback)
```

- [ ] **Step 2: Verify RED**

Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurement_cv.py::test_process_adds_low_confidence_contour_fallback_when_line_detection_misses_boundary -q`.

Expected: FAIL because no fallback exists.

- [ ] **Step 3: Implement minimum behavior**

```python
def contour_straight_candidates(contour, min_length):
    perimeter = cv2.arcLength(contour, True)
    polygon = cv2.approxPolyDP(contour, 0.005 * perimeter, True).reshape(-1, 2)
    return [make_contour_candidate(a, b, index) for index, (a, b) in enumerate(zip(polygon, np.roll(polygon, -1, axis=0)), 1) if np.linalg.norm(b - a) >= min_length]


def make_contour_candidate(point_a, point_b, index):
    candidate = _line_candidate([*point_a, *point_b], 1, 1, "contour_fallback", f"CF{index}")
    return {**candidate, "confidence": 0.45, "fallback": True}
```

Append only if no normal logical edge is within 4 degrees and 8 pixels. Fallback cannot become corner-radius evidence; selecting it stays `REVIEW`.

- [ ] **Step 4: Verify GREEN and commit**

Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurement_cv.py -q`; expected PASS. Commit with `feat: add contour fallback edge candidates`.

### Task 4: Jig geometry validation and diagnostics

**Files:** Modify `qc_server/app/routers/measurements.py`, `qc_server/app/schemas.py`, `qc_server/tests/test_measurements.py`, `qc_frontend/src/views/MeasurementStudio.vue`, `qc_frontend/src/views/__tests__/MeasurementStudio.test.js`, and both locale files.

**Interfaces:** Process response adds `diagnostics = {"variants": dict, "candidate_counts": dict, "contour_found": bool}`. `_detect_green_jig(frame)` returns HTTP 422 for invalid top-down quadrilateral.

- [ ] **Step 1: Write failing tests**

```python
def test_detect_jig_rejects_points_that_are_not_a_top_down_rectangle(client):
    response = client.post("/api/measurements/detect-jig", files={"file": ("skew.png", _skewed_jig_png_bytes(), "image/png")})
    assert response.status_code == 422
```

```js
it('shows diagnostics only in collapsed engineering details', async () => {
  mocks.processMeasurement.mockResolvedValue({ ...processed(), diagnostics: { candidate_counts: { lsd_raw: 2 } } })
  const wrapper = mount(MeasurementStudio)
  await stage(wrapper)
  await calibrate(wrapper)
  await wrapper.find('.process-measurement').trigger('click')
  await flushPromises()
  expect(wrapper.find('.measurement-diagnostics details').exists()).toBe(true)
})
```

- [ ] **Step 2: Verify RED**

Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurements.py -q` and `npm test -- --run src/views/__tests__/MeasurementStudio.test.js`.

Expected: both assertions fail.

- [ ] **Step 3: Implement minimum behavior**

After sorting jig points, require top/bottom angle within 10 degrees of horizontal, left/right within 10 degrees of vertical, and opposite-side length difference ratio at most `0.15`. Return `422 "green jig points do not form a top-down rectangle"` otherwise. Return detector counts and Canny values from `process_image()`. Render only collapsed engineering diagnostics; do not add threshold controls.

- [ ] **Step 4: Verify GREEN and commit**

Run the two focused suites above; expected PASS. Commit with `feat: validate jig geometry and expose diagnostics`.

### Task 5: Stage 00 raw fixture and I6 checkpoint

**Files:** Create `qc_server/tests/fixtures/measurement/stage00-hvs/README.md`; modify `qc_server/tests/test_measurements.py`, feature PRD/milestones, `CHANGELOG.md`, and `AGENTS.md`.

**Fixture contract:** record filename, source, resolution, flash state, autofocus/exposure settle time, independent X/Y dimensions, expected visible edges, and expected `REVIEW` edges. Never record a production accuracy claim.

- [ ] **Step 1: Create fixture contract and add regression after raw JPEG exists**

```python
from pathlib import Path


def _fixture_bytes(name):
    return (Path(__file__).parent / "fixtures" / "measurement" / name).read_bytes()


def _fixture_calibration():
    return _axes_calibration()


def test_stage00_no_flash_fixture_returns_expected_visible_edges(client):
    response = client.post("/api/measurements/process", files={"file": ("no-flash.jpg", _fixture_bytes("stage00-hvs/no-flash.jpg"), "image/jpeg")}, data={"calibration": _fixture_calibration()})
    assert response.status_code == 200
    assert len(response.json()["logical_edges"]) >= 3
```

- [ ] **Step 2: Verify fixture before any tuning**

Run `.\.venv\Scripts\python.exe -m pytest tests/test_measurements.py::test_stage00_no_flash_fixture_returns_expected_visible_edges -q`.

Expected: record observed edge count; do not tune from screenshot alone.

- [ ] **Step 3: Final verification and record I6**

Run `.\.venv\Scripts\python.exe -m pytest -q`, `npm test -- --run`, and `npm run build`.

Expected: all exit 0. Mark I6 complete only for detector robustness evidence; physical accuracy stays `PLANNED`. Commit with `docs: record stage00 measurement detector evidence`.

## Plan Self-Review

- Covered: raw download, adaptive multi-detector, contour fallback, jig validation, diagnostics, raw fixture, and milestone evidence.
- Excluded: AI model, CAD/PDF parser, manual CV threshold UI, and production accuracy claim.
- Controlled Bench remains required for physical accuracy/repeatability.
