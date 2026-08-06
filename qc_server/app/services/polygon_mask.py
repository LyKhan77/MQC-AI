import math
from numbers import Real

import cv2
import numpy as np


def validate_polygon(points, width, height) -> list[list[int]]:
    if len(points) < 3:
        raise ValueError("polygon requires at least three points")
    if width <= 0 or height <= 0:
        raise ValueError("polygon bounds must be positive")

    result = []
    for point in points:
        if len(point) != 2 or not all(isinstance(value, Real) and math.isfinite(value) for value in point):
            raise ValueError("polygon points must contain finite numeric values")
        x, y = point
        if not 0 <= x <= width or not 0 <= y <= height:
            raise ValueError("polygon point is outside image bounds")
        result.append([max(0, min(width, int(round(x)))), max(0, min(height, int(round(y))))])
    return result


def prepare_polygon_roi(frame, polygon) -> tuple[np.ndarray, tuple[int, int]]:
    height, width = frame.shape[:2]
    points = validate_polygon(polygon, width, height)
    x0 = min(point[0] for point in points)
    y0 = min(point[1] for point in points)
    x1 = max(point[0] for point in points)
    y1 = max(point[1] for point in points)
    roi = frame[y0:y1, x0:x1].copy()
    local = np.asarray([[[x - x0, y - y0] for x, y in points]], dtype=np.int32)
    mask = np.zeros(roi.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, local, 255)
    return cv2.bitwise_and(roi, roi, mask=mask), (x0, y0)


def remap_polygon(polygon, offset_x, offset_y) -> list[list[int]]:
    return [[int(x + offset_x), int(y + offset_y)] for x, y in polygon]


def polygon_has_overlap(candidate, mask) -> bool:
    if not candidate or mask.size == 0:
        return False
    height, width = mask.shape[:2]
    points = validate_polygon(candidate, width, height)
    candidate_mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(candidate_mask, [np.asarray(points, dtype=np.int32)], 255)
    return bool(np.any((mask != 0) & (candidate_mask != 0)))
