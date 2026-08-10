import cv2
import numpy as np

from app.services.measurement import calibrate_reference, process_image


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
