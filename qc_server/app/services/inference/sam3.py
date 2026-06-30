from __future__ import annotations

import math

from .base import Detection, DefectClassSpec, register

POLYGON_EPSILON = 2.0


def _perp_distance(p, a, b) -> float:
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    return abs(dy * x - dx * y + x2 * y1 - y2 * x1) / math.hypot(dx, dy)


def _rdp(points, epsilon):
    if len(points) < 3:
        return points
    start, end = points[0], points[-1]
    dmax, index = 0.0, 0
    for i in range(1, len(points) - 1):
        d = _perp_distance(points[i], start, end)
        if d > dmax:
            dmax, index = d, i
    if dmax > epsilon:
        left = _rdp(points[: index + 1], epsilon)
        right = _rdp(points[index:], epsilon)
        return left[:-1] + right
    return [start, end]


def simplify_polygon(points, epsilon, width, height):
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) < 3:
        return []
    simplified = _rdp(pts, epsilon)
    if len(simplified) < 3:
        return []
    out = []
    for x, y in simplified:
        cx = max(0, min(width, int(round(x))))
        cy = max(0, min(height, int(round(y))))
        out.append([cx, cy])
    return out


_predictor = None
_predictor_path = None


def get_predictor(model_path):
    global _predictor, _predictor_path
    if _predictor is None or _predictor_path != model_path:
        from ultralytics.models.sam import SAM3SemanticPredictor

        _predictor = SAM3SemanticPredictor(overrides=dict(
            conf=0.01,
            task="segment",
            mode="predict",
            model=model_path,
            half=True,
        ))
        _predictor_path = model_path
    return _predictor


class Sam3Strategy:
    name = "sam3_prompt"

    def detect(self, image_path, width, height, defect_classes, params):
        model_path = params.get("qc_model_path")
        if not model_path:
            raise ValueError(
                "No QC model selected (Settings -> QC / Segmentation Model)"
            )
        threshold = params.get("confidence_threshold", 0.5)

        predictor = get_predictor(model_path)
        predictor.set_image(image_path)

        detections: list[Detection] = []
        for spec in defect_classes:
            if not spec.enabled:
                continue
            for result in predictor(text=[spec.name]):
                masks = getattr(result, "masks", None)
                boxes = getattr(result, "boxes", None)
                if masks is None or boxes is None:
                    continue
                for poly, conf in zip(masks.xy, boxes.conf):
                    score = float(conf)
                    if score < threshold:
                        continue
                    polygon = simplify_polygon(poly, POLYGON_EPSILON, width, height)
                    if not polygon:
                        continue
                    detections.append(Detection(
                        type=spec.name,
                        category=spec.category,
                        confidence=round(score, 2),
                        polygon=polygon,
                    ))
        return detections


register(Sam3Strategy())
