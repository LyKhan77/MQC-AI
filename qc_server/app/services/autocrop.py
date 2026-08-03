import cv2
import numpy as np

_MIN_FRAC = 0.02
_MAX_FRAC = 0.92


def _analyze(frame):
    h, w = frame.shape[:2]
    area = float(h * w)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if int(np.count_nonzero(mask)) > mask.size / 2:
        mask = cv2.bitwise_not(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return frame, None, 0, 0
    candidates = [contour for contour in contours if cv2.contourArea(contour) / area >= _MIN_FRAC]
    x, y, bw, bh = cv2.boundingRect(max(contours, key=cv2.contourArea))
    frac = (bw * bh) / area
    if frac < _MIN_FRAC or frac > _MAX_FRAC:
        return frame, None, len(candidates)
    return frame[y : y + bh, x : x + bw].copy(), [x, y, x + bw, y + bh], len(candidates)


def autocrop(frame):
    """Isolate one dominant foreground part, or return full frame."""
    cropped, box, *_ = _analyze(frame)
    return cropped, box


def analyze_autocrop(frame):
    return _analyze(frame)


def assess_crop(frame, box, candidate_count=None):
    """Return a small operator-facing quality gate for an auto-crop box."""
    h, w = frame.shape[:2]
    if not box:
        return {"status": "reject", "reason": "no_object", "coverage": 0.0, "edge_margin": 0.0, "candidate_count": candidate_count or 0}
    x1, y1, x2, y2 = box
    coverage = max(0, x2 - x1) * max(0, y2 - y1) / float(w * h)
    edge_margin = min(x1, y1, w - x2, h - y2) / float(min(w, h))
    if edge_margin <= 0:
        status, reason = "reject", "object_touches_edge"
    elif candidate_count and candidate_count > 1:
        status, reason = "review", "multiple_objects"
    elif edge_margin < 0.01:
        status, reason = "review", "object_near_edge"
    else:
        status, reason = "ok", "stable_box"
    return {
        "status": status,
        "reason": reason,
        "coverage": round(coverage, 4),
        "edge_margin": round(max(0.0, edge_margin), 4),
        "candidate_count": candidate_count or 1,
    }
