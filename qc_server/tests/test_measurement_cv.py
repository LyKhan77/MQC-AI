import cv2
import numpy as np

import app.services.measurement as measurement

from app.services.measurement import (
    calibrate_axes,
    calibrate_reference,
    detect_component_contour,
    detect_corner_arcs,
    fit_circle,
    fit_logical_edges,
    detect_hole_candidates,
    group_line_candidates,
    process_image,
)


def _calibration():
    return calibrate_reference((0, 0), (100, 0), 50)


def _axes_calibration():
    return calibrate_axes(
        {"point_a": [0, 0], "point_b": [100, 0], "known_mm": 50},
        {"point_a": [0, 0], "point_b": [0, 100], "known_mm": 50},
        "independent_artifact",
    )


def test_fit_circle_returns_radius_and_low_residual():
    radians = np.linspace(0, np.pi / 2, 40)
    points = np.column_stack((20 + 10 * np.cos(radians), 30 + 10 * np.sin(radians)))

    center, radius, residual = fit_circle(points)

    assert np.allclose(center, [20, 30], atol=0.1)
    assert abs(radius - 10) <= 0.1
    assert residual <= 0.1


def _kasa_radius(points):
    matrix = np.column_stack((2 * points[:, 0], 2 * points[:, 1], np.ones(len(points))))
    target = points[:, 0] ** 2 + points[:, 1] ** 2
    solution, *_ = np.linalg.lstsq(matrix, target, rcond=None)
    return float(np.sqrt(max(solution[2] + solution[0] ** 2 + solution[1] ** 2, 0)))


def test_fit_circle_taubin_accurate_on_short_arc():
    rng = np.random.default_rng(7)
    radians = np.linspace(0, np.radians(45), 60)
    points = np.column_stack((100 * np.cos(radians), 100 * np.sin(radians)))
    points = points + rng.normal(0, 0.8, points.shape)

    center, radius, residual = fit_circle(points)

    taubin_error = abs(radius - 100)
    kasa_error = abs(_kasa_radius(points) - 100)
    assert taubin_error <= 4.0
    assert taubin_error < kasa_error


def test_detect_corner_arcs_returns_calibrated_rounded_rectangle_corners():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    mask = np.zeros((240, 320), dtype=np.uint8)
    radius = 24
    cv2.rectangle(mask, (60 + radius, 40), (260 - radius, 200), 255, -1)
    cv2.rectangle(mask, (60, 40 + radius), (260, 200 - radius), 255, -1)
    for center in ((84, 64), (236, 64), (84, 176), (236, 176)):
        cv2.circle(mask, center, radius, 255, -1)
    frame[mask > 0] = (255, 255, 255)
    contour = detect_component_contour(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

    candidates = detect_corner_arcs(contour, _axes_calibration())

    assert len(candidates) >= 4
    nearest = min(candidates, key=lambda item: np.linalg.norm(np.asarray(item["center"]) - np.asarray([84, 64])))
    assert np.linalg.norm(np.asarray(nearest["center"]) - np.asarray([84, 64])) <= 4
    assert 10 <= nearest["radius_mm"] <= 14
    assert 45 <= nearest["coverage_deg"] <= 120
    assert nearest["confidence"] >= 0.5


def test_detect_corner_arcs_rejects_radius_below_configured_minimum():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    mask = np.zeros((240, 320), dtype=np.uint8)
    radius = 24
    cv2.rectangle(mask, (60 + radius, 40), (260 - radius, 200), 255, -1)
    cv2.rectangle(mask, (60, 40 + radius), (260, 200 - radius), 255, -1)
    for center in ((84, 64), (236, 64), (84, 176), (236, 176)):
        cv2.circle(mask, center, radius, 255, -1)
    frame[mask > 0] = (255, 255, 255)
    contour = detect_component_contour(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

    candidates = detect_corner_arcs(contour, _axes_calibration(), {"corner_min_radius_mm": 13})

    assert candidates == []


def _rounded_rect_frame():
    frame = np.zeros((400, 400, 3), dtype=np.uint8)
    mask = np.zeros((400, 400), dtype=np.uint8)
    radius = 24
    cv2.rectangle(mask, (100 + radius, 130), (300 - radius, 290), 255, -1)
    cv2.rectangle(mask, (100, 130 + radius), (300, 290 - radius), 255, -1)
    for center in ((124, 154), (276, 154), (124, 266), (276, 266)):
        cv2.circle(mask, center, radius, 255, -1)
    frame[mask > 0] = (255, 255, 255)
    return frame


def test_corner_radius_stable_under_rotation():
    base = _rounded_rect_frame()
    estimates = []
    for angle in (0, 45, 90):
        frame = base if angle == 0 else cv2.warpAffine(
            base, cv2.getRotationMatrix2D((200, 200), angle, 1.0), (400, 400),
            flags=cv2.INTER_LINEAR)
        contour = detect_component_contour(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        candidates = detect_corner_arcs(contour, _axes_calibration())
        assert candidates, f"no corner candidate at {angle} degrees"
        nearest = min(candidates, key=lambda item: np.linalg.norm(
            np.asarray(item["center"]) - np.asarray([124, 154])))
        estimates.append(nearest["radius_mm"])
    assert all(10.0 <= value <= 14.0 for value in estimates)
    assert max(estimates) - min(estimates) <= 1.0


def test_logical_edge_endpoints_snap_to_virtual_corner():
    result = process_image(_rounded_rect_frame(), _axes_calibration(), task_types=["linear_dimension"])
    top = min(
        (edge for edge in result["logical_edges"] if abs(edge["angle"]) < 3),
        key=lambda edge: abs(edge["points"][0][1] - 130),
    )
    xs = sorted([top["points"][0][0], top["points"][1][0]])
    assert abs(xs[0] - 100) <= 3
    assert abs(xs[1] - 300) <= 3
    assert "virtual_intersection" in top["endpoint_sources"]


def test_group_line_candidates_merges_fragmented_collinear_segments():
    candidates = [
        {"id": "R1", "points": [[10, 20], [40, 20]], "angle": 0, "length_px": 30},
        {"id": "R2", "points": [[45, 20.5], [90, 20.5]], "angle": 0.2, "length_px": 45},
    ]

    assert len(group_line_candidates(candidates)) == 1


def test_group_line_candidates_keeps_parallel_boundaries_separate():
    candidates = [
        {"id": "R1", "points": [[10, 20], [90, 20]], "angle": 0, "length_px": 80},
        {"id": "R2", "points": [[10, 35], [90, 35]], "angle": 0, "length_px": 80},
    ]

    assert len(group_line_candidates(candidates)) == 2


def test_fit_logical_edges_does_not_extend_segment_to_unrelated_contour_extrema():
    edge_map = np.zeros((120, 140), dtype=np.uint8)
    edge_map[49:52, 20:81] = 255
    contour = np.asarray([[[0, 0]], [[100, 0]], [[100, 100]], [[0, 100]]], dtype=np.float32)
    groups = [[{"id": "R1", "points": [[20, 50], [80, 50]], "length_px": 60}]]

    result = fit_logical_edges(edge_map, contour, groups)

    assert len(result) == 1
    points = result[0]["points"]
    assert min(point[0] for point in points) >= 19
    assert max(point[0] for point in points) <= 81


def test_process_image_returns_logical_edge_spans_for_rounded_component():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    mask = np.zeros((240, 320), dtype=np.uint8)
    radius = 20
    cv2.rectangle(mask, (60 + radius, 40), (260 - radius, 200), 255, -1)
    cv2.rectangle(mask, (60, 40 + radius), (260, 200 - radius), 255, -1)
    for center in ((80, 60), (240, 60), (80, 180), (240, 180)):
        cv2.circle(mask, center, radius, 255, -1)
    frame[mask > 0] = (255, 255, 255)

    result = process_image(frame, _calibration())

    assert result["logical_edges"]
    assert len(result["logical_edges"]) <= len(result["candidates"])
    lengths = [edge["length_px"] for edge in result["logical_edges"]]
    assert max(lengths) >= 155
    # Virtual-corner endpoints span the full 200 px mold-line width.
    assert max(lengths) <= 205
    assert all(
        0 <= point[0] <= 320 and 0 <= point[1] <= 240
        for edge in result["logical_edges"]
        for point in edge["points"]
    )


def test_process_image_returns_line_candidates_for_clear_rectangle():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(frame, (40, 50), (280, 190), (255, 255, 255), 4)

    result = process_image(frame, _calibration())

    assert result["readiness"] == "ready"
    assert result["candidates"]
    assert all(candidate["source"].split("_")[0] in {"lsd", "hough"} for candidate in result["candidates"])
    assert all(candidate["confidence"] > 0 for candidate in result["candidates"])
    assert any(candidate["length_px"] > 100 for candidate in result["candidates"])


def test_adaptive_canny_uses_frame_intensity_not_fixed_thresholds():
    _, dark = measurement.adaptive_canny(np.full((120, 160), 35, dtype=np.uint8))
    _, bright = measurement.adaptive_canny(np.full((120, 160), 220, dtype=np.uint8))

    assert dark["low"] != bright["low"]


def test_process_keeps_hough_candidates_when_lsd_has_candidates():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(frame, (40, 50), (280, 190), (255, 255, 255), 4)

    result = process_image(frame, _calibration())

    assert any(item["source"].startswith("lsd_") for item in result["candidates"])
    assert any(item["source"].startswith("hough_") for item in result["candidates"])


def test_process_adds_low_confidence_contour_fallback_when_line_detection_misses_boundary(monkeypatch):
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(frame, (40, 50), (280, 190), (255, 255, 255), 4)
    monkeypatch.setattr(
        measurement,
        "line_candidates_from_variants",
        lambda gray, min_length: ([], np.zeros_like(gray)),
    )

    result = process_image(frame, _calibration())

    fallback = [item for item in result["candidates"] if item["source"] == "contour_fallback"]
    assert fallback
    assert all(item["confidence"] <= 0.45 for item in fallback)
    assert any(item.get("source") == "contour_fallback" for item in result["logical_edges"])


def test_process_image_collapses_thick_stroke_duplicates_to_outer_edges():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(frame, (40, 50), (280, 190), (255, 255, 255), 8)

    result = process_image(frame, _calibration())

    assert len(result["logical_edges"]) == 4


def test_process_image_returns_review_for_empty_frame():
    frame = np.zeros((120, 160, 3), dtype=np.uint8)

    result = process_image(frame, _calibration())

    assert result["readiness"] == "review"
    assert result["reason"] == "no_usable_edge"
    assert result["candidates"] == []


def test_detect_hole_candidates_returns_center_and_radius_for_clean_circle():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.circle(frame, (160, 120), 36, (255, 255, 255), -1)

    holes = detect_hole_candidates(frame, {"min_radius_px": 30, "max_radius_px": 42})

    assert holes
    hole = min(holes, key=lambda value: abs(value["center"][0] - 160) + abs(value["center"][1] - 120))
    assert abs(hole["center"][0] - 160) <= 2
    assert abs(hole["center"][1] - 120) <= 2
    assert 32 <= hole["radius_px"] <= 40
    assert hole["diameter_px"] == hole["radius_px"] * 2
    assert hole["source"] in {"hough_circle_alt", "hough_circle"}
    assert hole["confidence"] > 0


def test_process_image_returns_holes_for_hole_task():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.circle(frame, (160, 120), 36, (255, 255, 255), -1)

    result = process_image(
        frame,
        _calibration(),
        {"min_radius_px": 30, "max_radius_px": 42},
        task_type="hole_diameter",
        view_type="top",
    )

    assert result["readiness"] == "ready"
    assert result["holes"]
