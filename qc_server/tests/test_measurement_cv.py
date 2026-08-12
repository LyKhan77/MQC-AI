import cv2
import numpy as np

from app.services.measurement import (
    calibrate_reference,
    detect_hole_candidates,
    group_line_candidates,
    process_image,
)


def _calibration():
    return calibrate_reference((0, 0), (100, 0), 50)


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


def test_process_image_returns_logical_outer_edges_for_rounded_component():
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
    assert max(edge["length_px"] for edge in result["logical_edges"]) >= 195
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
    assert all(candidate["source"] in {"lsd", "hough"} for candidate in result["candidates"])
    assert all(candidate["confidence"] > 0 for candidate in result["candidates"])
    assert any(candidate["length_px"] > 100 for candidate in result["candidates"])


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
