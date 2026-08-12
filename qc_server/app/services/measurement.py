from math import acos, atan2, degrees, hypot

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
POSE_TYPES = {"TOP_FACE", "REVERSE_FACE", "PROFILE_FACE", "CUSTOM_FACE"}
MIN_CONFIDENCE = 0.5


def _point(value):
    if not isinstance(value, (list, tuple, np.ndarray)) or len(value) != 2:
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


def _reference_payload(reference, axis):
    if not isinstance(reference, dict):
        raise ValueError(f"{axis} reference is required")
    point_a = reference.get("point_a")
    point_b = reference.get("point_b")
    known_mm = float(reference.get("known_mm", 0))
    reference_px = _distance(point_a, point_b)
    if reference_px < 10:
        raise ValueError(f"{axis} reference is too short")
    angle = degrees(atan2(abs(_point(point_b)[1] - _point(point_a)[1]), abs(_point(point_b)[0] - _point(point_a)[0])))
    if axis == "x" and angle > 10:
        raise ValueError("horizontal reference must be within 10 degrees of horizontal")
    if axis == "y" and angle < 80:
        raise ValueError("vertical reference must be within 10 degrees of vertical")
    if known_mm <= 0:
        raise ValueError("known length must be positive")
    return {
        "point_a": [float(_point(point_a)[0]), float(_point(point_a)[1])],
        "point_b": [float(_point(point_b)[0]), float(_point(point_b)[1])],
        "known_mm": known_mm,
        "reference_px": reference_px,
    }


def calibrate_axes(x_reference, y_reference, source):
    if source not in {"independent_artifact", "component_demo"}:
        raise ValueError("invalid calibration source")
    x = _reference_payload(x_reference, "x")
    y = _reference_payload(y_reference, "y")
    scale_x = x["known_mm"] / x["reference_px"]
    scale_y = y["known_mm"] / y["reference_px"]
    return {
        "mode": "manual_axes",
        "source": source,
        "x": x,
        "y": y,
        "scale_x_mm_per_px": scale_x,
        "scale_y_mm_per_px": scale_y,
        "valid": True,
        "verdict_eligible": source == "independent_artifact",
    }


def calibration_scales(calibration):
    if not calibration or not calibration.get("valid"):
        raise ValueError("invalid calibration")
    if calibration.get("mode") == "manual_axes":
        scale_x = float(calibration.get("scale_x_mm_per_px", 0))
        scale_y = float(calibration.get("scale_y_mm_per_px", 0))
    else:
        scale_x = scale_y = float(calibration.get("mm_per_pixel", 0))
    if scale_x <= 0 or scale_y <= 0:
        raise ValueError("invalid calibration scale")
    return scale_x, scale_y


def scaled_distance(point_a, point_b, calibration):
    ax, ay = _point(point_a)
    bx, by = _point(point_b)
    scale_x, scale_y = calibration_scales(calibration)
    return hypot((bx - ax) * scale_x, (by - ay) * scale_y)


def calibration_verdict_eligible(calibration):
    if not calibration or not calibration.get("valid"):
        return False
    if calibration.get("mode") == "manual_axes":
        return calibration.get("source") == "independent_artifact"
    return True


def _calibration_scale(calibration):
    scale_x, scale_y = calibration_scales(calibration)
    return (scale_x + scale_y) / 2


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


def pose_task_supported(task_type, pose_type):
    if pose_type not in POSE_TYPES:
        return False
    if task_type in PROFILE_TASK_TYPES:
        return pose_type == "PROFILE_FACE"
    return task_type in LINEAR_TYPES or task_type in SUPPORTED_TASK_TYPES


def profile_supports_measurement(profile, nominal, measured=None):
    if not isinstance(profile, dict) or nominal is None:
        return False
    capability = profile.get("capability")
    if not isinstance(capability, dict):
        return False
    try:
        requested = float(nominal if measured is None else measured)
        minimum = float(capability.get("minimum_supported_feature_mm", 0))
        maximum = float(capability.get("maximum_supported_span_mm", 0))
    except (TypeError, ValueError):
        return False
    if requested <= 0 or minimum < 0 or maximum < 0:
        return False
    if minimum and requested < minimum:
        return False
    if maximum and requested > maximum:
        return False
    return True


def validate_measurement_profile(profile, frame_width, frame_height, source_camera_id=None):
    if not isinstance(profile, dict):
        return {"valid": False, "reason": "missing_profile"}
    if profile.get("status") not in {"valid", "approved"}:
        return {"valid": False, "reason": "invalid_profile_status"}
    try:
        width = int(profile.get("resolution_width", 0))
        height = int(profile.get("resolution_height", 0))
    except (TypeError, ValueError):
        return {"valid": False, "reason": "invalid_profile_resolution"}
    if width and height and (width != int(frame_width) or height != int(frame_height)):
        return {"valid": False, "reason": "profile_resolution_mismatch"}
    profile_camera_id = profile.get("camera_id")
    if profile_camera_id and source_camera_id and profile_camera_id != source_camera_id:
        return {"valid": False, "reason": "profile_camera_mismatch"}
    calibration = profile.get("calibration")
    if not isinstance(calibration, dict) or not calibration.get("valid"):
        return {"valid": False, "reason": "invalid_calibration"}
    try:
        if float(calibration.get("mm_per_pixel", 0)) <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return {"valid": False, "reason": "invalid_calibration"}
    return {
        "valid": True,
        "reason": "",
        "profile_id": profile.get("id"),
        "calibration": calibration,
    }


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
        value = scaled_distance(points[0], points[1], calibration)
    elif item_type == "hole_diameter":
        value = pixel_value * scale * 2
    else:
        raise ValueError("unsupported measurement type")
    return {"value": value, "unit": "mm", "pixel_value": pixel_value}


def _line_candidate(line, width, height, source, identifier=None, metadata=None):
    x1, y1, x2, y2 = [float(value) for value in line]
    length = hypot(x2 - x1, y2 - y1)
    if length <= 0:
        return None
    diagonal = hypot(width, height)
    confidence = min(0.99, 0.5 + (length / max(diagonal, 1)) * 0.5)
    return {
        "id": identifier or f"{source}-{round(x1, 2)}-{round(y1, 2)}",
        "points": [[round(x1, 2), round(y1, 2)], [round(x2, 2), round(y2, 2)]],
        "length_px": round(length, 3),
        "angle": round(degrees(np.arctan2(y2 - y1, x2 - x1)), 3),
        "confidence": round(confidence, 3),
        "source": source,
        **({key: value for key, value in (metadata or {}).items() if value is not None}),
    }


def _candidate_angle(candidate):
    first, second = candidate["points"]
    return degrees(np.arctan2(float(second[1]) - float(first[1]), float(second[0]) - float(first[0]))) % 180


def _angle_delta(first, second):
    delta = abs((first - second) % 180)
    return min(delta, 180 - delta)


def _line_direction(point_a, point_b):
    ax, ay = _point(point_a)
    bx, by = _point(point_b)
    length = hypot(bx - ax, by - ay)
    if length <= 0:
        raise ValueError("edge points must be different")
    return np.array([(bx - ax) / length, (by - ay) / length], dtype=np.float32)


def _line_distance(point, line_a, line_b):
    px, py = _point(point)
    ax, ay = _point(line_a)
    bx, by = _point(line_b)
    dx, dy = bx - ax, by - ay
    length = hypot(dx, dy)
    if length <= 0:
        raise ValueError("edge points must be different")
    return abs((px - ax) * dy - (py - ay) * dx) / length


def _projected_gap(first, second, direction):
    first_values = [float(np.dot(np.asarray(point, dtype=np.float32), direction)) for point in first["points"]]
    second_values = [float(np.dot(np.asarray(point, dtype=np.float32), direction)) for point in second["points"]]
    first_min, first_max = min(first_values), max(first_values)
    second_min, second_max = min(second_values), max(second_values)
    return max(0.0, second_min - first_max, first_min - second_max)


def _line_candidates_compatible(first, second, options):
    if _angle_delta(_candidate_angle(first), _candidate_angle(second)) > float(options["angle_tolerance_deg"]):
        return False
    direction = _line_direction(first["points"][0], first["points"][1])
    midpoint = [
        (float(second["points"][0][0]) + float(second["points"][1][0])) / 2,
        (float(second["points"][0][1]) + float(second["points"][1][1])) / 2,
    ]
    if _line_distance(midpoint, first["points"][0], first["points"][1]) > float(options["support_distance_px"]):
        return False
    return _projected_gap(first, second, direction) <= float(options["projected_gap_px"])


def group_line_candidates(candidates, options=None):
    options = {
        "angle_tolerance_deg": 3.0,
        "support_distance_px": 4.0,
        "projected_gap_px": 12.0,
        **(options or {}),
    }
    groups = []
    for candidate in candidates or []:
        for group in groups:
            if any(_line_candidates_compatible(candidate, member, options) for member in group):
                group.append(candidate)
                break
        else:
            groups.append([candidate])
    return groups


def detect_component_contour(gray):
    if gray is None or len(gray.shape) != 2:
        raise ValueError("invalid grayscale frame")
    height, width = gray.shape[:2]
    frame_area = float(height * width)
    threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    kernel = np.ones((3, 3), dtype=np.uint8)
    masks = [
        cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel),
        cv2.morphologyEx(cv2.bitwise_not(threshold), cv2.MORPH_CLOSE, kernel),
    ]
    best = None
    for mask in masks:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < frame_area * 0.01 or area > frame_area * 0.95:
                continue
            x, y, contour_width, contour_height = cv2.boundingRect(contour)
            touches_all_borders = (
                x <= 0
                and y <= 0
                and x + contour_width >= width
                and y + contour_height >= height
            )
            if touches_all_borders:
                continue
            if best is None or area > best[0]:
                best = (area, contour)
    return best[1] if best else None


def fit_logical_edges(edge_map, contour, groups, options=None):
    options = {
        "support_band_px": 3.0,
        "support_gap_px": 12.0,
        "min_coverage_ratio": 0.25,
        **(options or {}),
    }
    edge_points = np.column_stack(np.where(edge_map > 0))[:, ::-1].astype(np.float32) if np.any(edge_map > 0) else np.empty((0, 2), dtype=np.float32)
    contour_points = contour.reshape(-1, 2).astype(np.float32) if contour is not None else None
    logical_edges = []
    for index, group in enumerate(groups or [], start=1):
        seed = max(group, key=lambda item: float(item.get("length_px", 0)))
        seed_a, seed_b = seed["points"]
        direction = _line_direction(seed_a, seed_b)
        support = []
        for point in edge_points:
            distance = _line_distance(point, seed_a, seed_b)
            projection = float(np.dot(point, direction))
            seed_projections = [float(np.dot(np.asarray(value, dtype=np.float32), direction)) for member in group for value in member["points"]]
            if distance <= float(options["support_band_px"]) and min(seed_projections) - float(options["support_gap_px"]) <= projection <= max(seed_projections) + float(options["support_gap_px"]):
                support.append(point)
        fit_points = np.asarray(support, dtype=np.float32) if len(support) >= 2 else np.asarray([point for member in group for point in member["points"]], dtype=np.float32)
        try:
            vx, vy, x0, y0 = cv2.fitLine(fit_points, cv2.DIST_HUBER, 0, 0.01, 0.01).reshape(-1)
            fitted_direction = np.array([float(vx), float(vy)], dtype=np.float32)
            fitted_direction /= max(float(np.linalg.norm(fitted_direction)), 1e-9)
        except cv2.error:
            fitted_direction = direction
            x0, y0 = fit_points.mean(axis=0)
        if float(np.dot(fitted_direction, direction)) < 0:
            fitted_direction *= -1
        origin = np.array([float(x0), float(y0)], dtype=np.float32)
        if contour_points is not None and len(contour_points) >= 3:
            values = np.dot(contour_points - origin, fitted_direction)
        else:
            group_points = np.asarray([point for member in group for point in member["points"]], dtype=np.float32)
            values = np.dot(group_points - origin, fitted_direction)
        low, high = float(values.min()), float(values.max())
        support_values = np.dot(fit_points - origin, fitted_direction)
        coverage_ratio = min(1.0, max(0.0, (float(support_values.max()) - float(support_values.min())) / max(high - low, 1e-6)))
        if contour_points is not None and coverage_ratio < float(options["min_coverage_ratio"]):
            continue
        point_a = origin + fitted_direction * low
        point_b = origin + fitted_direction * high
        offsets = fit_points - origin
        residual_values = offsets[:, 0] * fitted_direction[1] - offsets[:, 1] * fitted_direction[0]
        residual = float(np.mean(np.abs(residual_values))) if len(fit_points) else 99.0
        support_score = min(1.0, len(support) / 40.0)
        coverage_score = min(1.0, coverage_ratio / 0.75)
        residual_score = max(0.0, 1.0 - residual / 5.0)
        confidence = min(0.99, max(0.1, 0.3 * support_score + 0.25 * coverage_score + 0.45 * residual_score))
        points = [[round(float(point_a[0]), 2), round(float(point_a[1]), 2)], [round(float(point_b[0]), 2), round(float(point_b[1]), 2)]]
        logical_edges.append({
            "id": f"LE{index}",
            "points": points,
            "support_points": points,
            "direction": [round(float(fitted_direction[0]), 6), round(float(fitted_direction[1]), 6)],
            "length_px": round(float(np.linalg.norm(point_b - point_a)), 3),
            "angle": round(degrees(np.arctan2(float(fitted_direction[1]), float(fitted_direction[0]))), 3),
            "residual_px": round(residual, 4),
            "coverage_ratio": round(coverage_ratio, 4),
            "confidence": round(confidence, 3),
            "source_candidate_ids": [member.get("id") for member in group],
            "geometry": {"kind": "outer_span" if contour_points is not None else "line", "points": points},
        })
    return logical_edges


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
    detector = cv2.createLineSegmentDetector(cv2.LSD_REFINE_ADV)
    detected = detector.detect(gray)
    detected_lines = detected[0] if detected else None
    widths = detected[1] if len(detected) > 1 else None
    precisions = detected[2] if len(detected) > 2 else None
    nfas = detected[3] if len(detected) > 3 else None
    if detected_lines is not None:
        for index, line in enumerate(detected_lines):
            metadata = {
                "width_px": float(widths[index][0]) if widths is not None and len(widths) > index else None,
                "precision": float(precisions[index][0]) if precisions is not None and len(precisions) > index else None,
                "nfa": float(nfas[index][0]) if nfas is not None and len(nfas) > index else None,
            }
            raw_lines.append((line[0], "lsd", metadata))

    candidates = []
    for index, (line, source, metadata) in enumerate(raw_lines, start=1):
        candidate = _line_candidate(line, width, height, source, f"R{index}", metadata)
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
            for index, line in enumerate(detected[:, 0, :], start=len(candidates) + 1):
                candidate = _line_candidate(line, width, height, "hough", f"R{index}")
                if candidate and candidate["length_px"] >= min_length:
                    candidates.append(candidate)

    candidates.sort(key=lambda item: item["length_px"], reverse=True)
    candidates = candidates[:100]
    contour = detect_component_contour(gray)
    groups = group_line_candidates(candidates, options)
    edge_map = cv2.Canny(gray, 50, 150)
    logical_edges = fit_logical_edges(edge_map, contour, groups, options)
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
        "logical_edges": logical_edges,
        "holes": holes,
        "task_type": task_type,
        "view_type": view_type,
    }


def evaluate_item(
    measured,
    unit,
    nominal,
    tolerance,
    confidence,
    calibration_valid,
    task_type=None,
    view_type="top",
    calibration_reason="invalid_calibration",
):
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
        reason = calibration_reason
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
