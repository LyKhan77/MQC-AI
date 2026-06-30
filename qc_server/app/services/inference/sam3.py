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
