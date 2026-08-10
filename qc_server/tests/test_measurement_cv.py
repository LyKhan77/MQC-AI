import cv2
import numpy as np

from app.services.measurement import calibrate_reference, detect_hole_candidates, process_image


def _calibration():
    return calibrate_reference((0, 0), (100, 0), 50)


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
