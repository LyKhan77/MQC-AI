from math import acos, degrees, hypot

import cv2
import numpy as np


LINEAR_TYPES = {"edge_length", "edge_to_edge", "point_to_point", "linear_dimension"}
SUPPORTED_TASK_TYPES = {
    "linear_dimension",
    "thickness_profile",
    "bend_angle",
    "inclination",
    "hole_diameter",
    "hole_center_distance",
    "hole_edge_distance",
    "hole_center_to_edge",
}
SUPPORTED_VIEW_TYPES = {"top", "profile", "side"}
PROFILE_TASK_TYPES = {"thickness_profile", "bend_angle"}
MIN_CONFIDENCE = 0.5


def _point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("point must contain x and y")
    return float(value[0]), float(value[1])


def _distance(point_a, point_b):
    ax, ay = _point(point_a)
    bx, by = _point(point_b)
    return hypot(bx - ax, by - ay)


def _distance_point_to_segment(point, segment_a, segment_b):
    px, py = _point(point)
    ax, ay = _point(segment_a)
    bx, by = _point(segment_b)
    dx, dy = bx - ax, by - ay
    length_squared = dx * dx + dy * dy
    if length_squared <= 0:
        raise ValueError("edge points must be different")
    ratio = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_squared))
    return hypot(px - (ax + ratio * dx), py - (ay + ratio * dy))


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


def task_requires_profile(task_type):
    return task_type in PROFILE_TASK_TYPES


def task_view_supported(task_type, view_type):
    if task_type in LINEAR_TYPES:
        return view_type in SUPPORTED_VIEW_TYPES
    if task_type not in SUPPORTED_TASK_TYPES or view_type not in SUPPORTED_VIEW_TYPES:
        return False
    if task_requires_profile(task_type):
        return view_type in {"profile", "side"}
    return True


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


def measure_geometry(item_type, points, calibration, geometry=None):
    if item_type in {"angle", "bend_angle"}:
        if len(points) != 4:
            raise ValueError("angle requires four points")
        return {"value": _angle_degrees(points), "unit": "deg", "pixel_value": None}
    if item_type == "inclination":
        if len(points) != 2:
            raise ValueError("inclination requires two points")
        ax, ay = _point(points[0])
        bx, by = _point(points[1])
        value = abs(degrees(np.arctan2(by - ay, bx - ax)))
        value = value if value <= 90 else 180 - value
        return {"value": value, "unit": "deg", "pixel_value": None}

    scale = _calibration_scale(calibration)
    if geometry and geometry.get("kind") == "circle":
        center = _point(geometry.get("center"))
        radius_px = float(geometry.get("radius_px", 0))
        if radius_px <= 0:
            raise ValueError("circle radius must be positive")
        diameter_px = radius_px * 2
        return {
            "value": diameter_px * scale,
            "unit": "mm",
            "pixel_value": diameter_px,
            "geometry": {
                "kind": "circle",
                "center": [center[0], center[1]],
                "radius_px": radius_px,
            },
        }
    if geometry and geometry.get("kind") == "circle_to_edge":
        center = _point(geometry.get("center"))
        edge_a = _point(geometry.get("edge_a"))
        edge_b = _point(geometry.get("edge_b"))
        pixel_value = _distance_point_to_segment(center, edge_a, edge_b)
        return {
            "value": pixel_value * scale,
            "unit": "mm",
            "pixel_value": pixel_value,
            "geometry": {
                "kind": "circle_to_edge",
                "center": [center[0], center[1]],
                "edge_a": [edge_a[0], edge_a[1]],
                "edge_b": [edge_b[0], edge_b[1]],
            },
        }
    if geometry and geometry.get("kind") == "circle_pair":
        center_a = _point(geometry.get("center_a"))
        center_b = _point(geometry.get("center_b"))
        center_distance_px = _distance(center_a, center_b)
        if center_distance_px <= 0:
            raise ValueError("circle centers must be different")
        radius_a_px = float(geometry.get("radius_a_px", 0))
        radius_b_px = float(geometry.get("radius_b_px", 0))
        if radius_a_px < 0 or radius_b_px < 0:
            raise ValueError("circle radii must be non-negative")
        pixel_value = center_distance_px
        if item_type == "hole_edge_distance":
            pixel_value -= radius_a_px + radius_b_px
            if pixel_value < 0:
                raise ValueError("hole edge distance cannot be negative")
        elif item_type != "hole_center_distance":
            raise ValueError("unsupported circle pair measurement type")
        return {
            "value": pixel_value * scale,
            "unit": "mm",
            "pixel_value": pixel_value,
            "geometry": {
                "kind": "circle_pair",
                "center_a": [center_a[0], center_a[1]],
                "center_b": [center_b[0], center_b[1]],
                "radius_a_px": radius_a_px,
                "radius_b_px": radius_b_px,
            },
        }
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


def _refine_circle_radius(gray, center, radius_px):
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    best = None
    for contour in contours:
        if len(contour) < 5:
            continue
        ellipse = cv2.fitEllipse(contour)
        ellipse_center = ellipse[0]
        axes = ellipse[1]
        distance = hypot(ellipse_center[0] - center[0], ellipse_center[1] - center[1])
        fitted_radius = (float(axes[0]) + float(axes[1])) / 4
        if fitted_radius <= 0 or distance > max(4, radius_px * 0.25):
            continue
        radius_error = abs(fitted_radius - radius_px) / max(radius_px, 1)
        score = distance + radius_error * radius_px
        if best is None or score < best[0]:
            best = (score, fitted_radius, ellipse_center)
    if best is None:
        return float(radius_px), center, 0.72
    _, fitted_radius, ellipse_center = best
    return fitted_radius, [float(ellipse_center[0]), float(ellipse_center[1])], 0.92


def detect_hole_candidates(frame, options=None):
    if frame is None or not hasattr(frame, "shape") or len(frame.shape) < 2:
        raise ValueError("invalid frame")
    options = options or {}
    gray = frame if len(frame.shape) == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 1.5)
    min_radius = int(options.get("min_radius_px", 3))
    max_radius = int(options.get("max_radius_px", 0))
    min_dist = float(options.get("min_circle_dist_px", max(min_radius * 2, 8)))
    alt_method = getattr(cv2, "HOUGH_GRADIENT_ALT", None)
    method = alt_method or cv2.HOUGH_GRADIENT
    if method == alt_method and alt_method is not None:
        param1 = float(options.get("circle_param1", 300))
        param2 = float(options.get("circle_param2", 0.9))
        dp = float(options.get("circle_dp", 1.5))
        source = "hough_circle_alt"
    else:
        param1 = float(options.get("circle_param1", 100))
        param2 = float(options.get("circle_param2", 20))
        dp = float(options.get("circle_dp", 1))
        source = "hough_circle"
    detected = cv2.HoughCircles(
        gray,
        method,
        dp,
        min_dist,
        param1=param1,
        param2=param2,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    if detected is None:
        return []
    height, width = gray.shape[:2]
    candidates = []
    for raw in detected[0]:
        x, y, radius = [float(value) for value in raw[:3]]
        if radius <= 0 or not (0 <= x < width and 0 <= y < height):
            continue
        refined_radius, refined_center, fit_confidence = _refine_circle_radius(gray, [x, y], radius)
        candidates.append({
            "center": [round(refined_center[0], 2), round(refined_center[1], 2)],
            "radius_px": round(refined_radius, 3),
            "diameter_px": round(refined_radius * 2, 3),
            "confidence": round(fit_confidence, 3),
            "source": source,
        })
    candidates.sort(key=lambda item: item["confidence"], reverse=True)
    return candidates[:100]


def process_image(frame, calibration, options=None, task_type="linear_dimension", view_type="top"):
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
    holes = detect_hole_candidates(frame, options) if task_type.startswith("hole_") else []
    calibration_valid = bool(calibration and calibration.get("valid"))
    if not task_view_supported(task_type, view_type):
        readiness = "review"
        reason = "unsupported_view"
    elif task_type.startswith("hole_") and not holes:
        readiness = "review"
        reason = "no_usable_hole"
    elif task_type.startswith("hole_") and not calibration_valid:
        readiness = "review"
        reason = "invalid_calibration"
    elif not candidates and not task_type.startswith("hole_"):
        readiness = "review"
        reason = "no_usable_edge"
    elif not calibration_valid:
        readiness = "review"
        reason = "invalid_calibration"
    else:
        readiness = "ready"
        reason = ""
    return {
        "readiness": readiness,
        "reason": reason,
        "candidates": candidates,
        "holes": holes,
        "task_type": task_type,
        "view_type": view_type,
    }


def evaluate_item(measured, unit, nominal, tolerance, confidence, calibration_valid, task_type=None, view_type="top"):
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
    if task_type and not task_view_supported(task_type, view_type):
        status = "REVIEW"
        reason = "unsupported_view"
    elif not calibration_valid:
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
