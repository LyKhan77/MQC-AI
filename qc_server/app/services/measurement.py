from math import acos, degrees, hypot

import cv2
import numpy as np


LINEAR_TYPES = {"edge_length", "edge_to_edge", "point_to_point"}
MIN_CONFIDENCE = 0.5


def _point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("point must contain x and y")
    return float(value[0]), float(value[1])


def _distance(point_a, point_b):
    ax, ay = _point(point_a)
    bx, by = _point(point_b)
    return hypot(bx - ax, by - ay)


def calibrate_reference(point_a, point_b, known_mm):
    known_mm = float(known_mm)
    reference_px = _distance(point_a, point_b)
    if reference_px <= 0:
        raise ValueError("reference points must be different")
    if known_mm <= 0:
        raise ValueError("known length must be positive")
    return {
        "reference_px": reference_px,
        "known_mm": known_mm,
        "mm_per_pixel": known_mm / reference_px,
        "px_per_mm": reference_px / known_mm,
        "valid": True,
    }


def _calibration_scale(calibration):
    if not calibration or not calibration.get("valid"):
        raise ValueError("invalid calibration")
    scale = float(calibration.get("mm_per_pixel", 0))
    if scale <= 0:
        raise ValueError("invalid calibration scale")
    return scale


def _angle_degrees(points):
    ax, ay = _point(points[0])
    bx, by = _point(points[1])
    cx, cy = _point(points[2])
    dx, dy = _point(points[3])
    first = (bx - ax, by - ay)
    second = (dx - cx, dy - cy)
    first_length = hypot(*first)
    second_length = hypot(*second)
    if first_length <= 0 or second_length <= 0:
        raise ValueError("angle lines must have length")
    dot = first[0] * second[0] + first[1] * second[1]
    cosine = max(-1.0, min(1.0, dot / (first_length * second_length)))
    return degrees(acos(cosine))


def measure_geometry(item_type, points, calibration):
    if item_type == "angle":
        if len(points) != 4:
            raise ValueError("angle requires four points")
        return {"value": _angle_degrees(points), "unit": "deg", "pixel_value": None}

    scale = _calibration_scale(calibration)
    if len(points) != 2:
        raise ValueError("linear measurement requires two points")
    pixel_value = _distance(points[0], points[1])
    if item_type in LINEAR_TYPES or item_type == "hole_center_distance":
        value = pixel_value * scale
    elif item_type == "hole_diameter":
        value = pixel_value * scale * 2
    else:
        raise ValueError("unsupported measurement type")
    return {"value": value, "unit": "mm", "pixel_value": pixel_value}


def _line_candidate(line, width, height, source):
    x1, y1, x2, y2 = [float(value) for value in line]
    length = hypot(x2 - x1, y2 - y1)
    if length <= 0:
        return None
    diagonal = hypot(width, height)
    confidence = min(0.99, 0.5 + (length / max(diagonal, 1)) * 0.5)
    return {
        "points": [[round(x1, 2), round(y1, 2)], [round(x2, 2), round(y2, 2)]],
        "length_px": round(length, 3),
        "angle": round(degrees(np.arctan2(y2 - y1, x2 - x1)), 3),
        "confidence": round(confidence, 3),
        "source": source,
    }


def process_image(frame, calibration, options=None):
    if frame is None or not hasattr(frame, "shape") or len(frame.shape) < 2:
        raise ValueError("invalid frame")
    options = options or {}
    height, width = frame.shape[:2]
    min_length = float(options.get("min_length_px", max(12, min(width, height) * 0.05)))
    gray = frame if len(frame.shape) == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    raw_lines = []
    detector = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    detected = detector.detect(gray)[0]
    if detected is not None:
        raw_lines.extend((line[0], "lsd") for line in detected)

    candidates = []
    for line, source in raw_lines:
        candidate = _line_candidate(line, width, height, source)
        if candidate and candidate["length_px"] >= min_length:
            candidates.append(candidate)

    if not candidates:
        edges = cv2.Canny(gray, 50, 150)
        detected = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            threshold=max(15, int(min_length / 2)),
            minLineLength=min_length,
            maxLineGap=max(4, int(min_length / 4)),
        )
        if detected is not None:
            for line in detected[:, 0, :]:
                candidate = _line_candidate(line, width, height, "hough")
                if candidate and candidate["length_px"] >= min_length:
                    candidates.append(candidate)

    candidates.sort(key=lambda item: item["length_px"], reverse=True)
    candidates = candidates[:100]
    calibration_valid = bool(calibration and calibration.get("valid"))
    if not candidates:
        readiness = "review"
        reason = "no_usable_edge"
    elif not calibration_valid:
        readiness = "review"
        reason = "invalid_calibration"
    else:
        readiness = "ready"
        reason = ""
    return {"readiness": readiness, "reason": reason, "candidates": candidates}


def evaluate_item(measured, unit, nominal, tolerance, confidence, calibration_valid):
    if nominal is None or tolerance is None:
        return {
            "measured": measured,
            "unit": unit,
            "nominal": nominal,
            "tolerance": tolerance,
            "min": None,
            "max": None,
            "deviation": None,
            "status": "REVIEW",
            "reason": "missing_nominal_or_tolerance",
        }
    nominal = float(nominal)
    tolerance = float(tolerance)
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    if not calibration_valid:
        status = "REVIEW"
        reason = "invalid_calibration"
    elif confidence < MIN_CONFIDENCE:
        status = "REVIEW"
        reason = "low_confidence"
    else:
        minimum = nominal - tolerance
        maximum = nominal + tolerance
        status = "PASS" if minimum <= measured <= maximum else "FAIL"
        reason = "" if status == "PASS" else "outside_tolerance"
    minimum = nominal - tolerance
    maximum = nominal + tolerance
    return {
        "measured": measured,
        "unit": unit,
        "nominal": nominal,
        "tolerance": tolerance,
        "min": minimum,
        "max": maximum,
        "deviation": measured - nominal,
        "status": status,
        "reason": reason,
    }
