import numpy as np

from app.services.autocrop import autocrop


def test_autocrop_bounds_bright_blob_on_dark_bg():
    frame = np.zeros((100, 100, 3), np.uint8)
    frame[30:70, 20:60] = 255
    cropped, box = autocrop(frame)
    assert box is not None
    x1, y1, x2, y2 = box
    assert abs(x1 - 20) <= 3 and abs(y1 - 30) <= 3
    assert abs(x2 - 60) <= 3 and abs(y2 - 70) <= 3
    assert cropped.shape[0] == y2 - y1 and cropped.shape[1] == x2 - x1


def test_autocrop_returns_full_frame_when_no_blob():
    frame = np.zeros((100, 100, 3), np.uint8)
    cropped, box = autocrop(frame)
    assert box is None
    assert cropped.shape == frame.shape
