import cv2
import numpy as np
import pytest

from app.services.polygon_mask import (
    polygon_has_overlap,
    prepare_polygon_roi,
    remap_polygon,
    validate_polygon,
)


def test_validate_polygon_rejects_fewer_than_three_points():
    with pytest.raises(ValueError, match="at least three"):
        validate_polygon([[1, 1], [5, 1]], 20, 20)


@pytest.mark.parametrize("points", [None, [1, 2, 3]])
def test_validate_polygon_rejects_malformed_points(points):
    with pytest.raises(ValueError, match="points"):
        validate_polygon(points, 20, 20)


def test_validate_polygon_rejects_zero_area_polygon():
    with pytest.raises(ValueError, match="area"):
        validate_polygon([[10, 10], [10, 15], [10, 20]], 40, 40)


def test_validate_polygon_rejects_out_of_bounds_points():
    with pytest.raises(ValueError, match="bounds"):
        validate_polygon([[1, 1], [19, 1], [21, 10]], 20, 20)


def test_prepare_roi_returns_bbox_offset_and_masked_pixels():
    frame = np.full((40, 50, 3), 255, dtype=np.uint8)
    roi, offset = prepare_polygon_roi(frame, [[10, 10], [30, 10], [30, 30], [10, 30]])
    assert offset == (10, 10)
    assert roi.shape[:2] == (20, 20)
    assert np.any(roi)


def test_remap_polygon_restores_original_coordinates():
    assert remap_polygon([[0, 0], [20, 0], [20, 20]], 10, 12) == [[10, 12], [30, 12], [30, 32]]


def test_polygon_has_overlap_detects_candidate_inside_mask():
    mask = np.zeros((20, 20), dtype=np.uint8)
    cv2.rectangle(mask, (5, 5), (10, 10), 255, -1)
    assert polygon_has_overlap([[6, 6], [8, 6], [8, 8]], mask)
    assert not polygon_has_overlap([[0, 0], [2, 0], [2, 2]], mask)
