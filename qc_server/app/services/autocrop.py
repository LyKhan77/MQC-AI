import cv2
import numpy as np

_MIN_FRAC = 0.02
_MAX_FRAC = 0.92


def autocrop(frame):
    """Isolate one dominant foreground part, or return full frame."""
    h, w = frame.shape[:2]
    area = float(h * w)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if int(np.count_nonzero(mask)) > mask.size / 2:
        mask = cv2.bitwise_not(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return frame, None
    x, y, bw, bh = cv2.boundingRect(max(contours, key=cv2.contourArea))
    frac = (bw * bh) / area
    if frac < _MIN_FRAC or frac > _MAX_FRAC:
        return frame, None
    return frame[y : y + bh, x : x + bw].copy(), [x, y, x + bw, y + bh]
