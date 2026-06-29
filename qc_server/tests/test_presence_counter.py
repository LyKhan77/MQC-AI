import numpy as np

from app.services.presence_counter import PresenceCounter
from app.services.object_detection import Detection


class FakeSession:
    def __init__(self):
        self.captures = []

    def add_captured(self, frame, detections, scale=1.0):
        self.captures.append(list(detections))
        return [f"obj_{i}.jpg" for i in range(len(detections))]


def _frame():
    return np.zeros((100, 100, 3), dtype=np.uint8)


def _big(conf=0.9):
    return Detection(10, 10, 60, 60, "o", conf)


def test_counts_and_crops_once_after_debounce():
    s = FakeSession()
    pc = PresenceCounter(s, present_frames=3, absent_frames=2)
    assert pc.update(_frame(), [_big()]) == 0
    assert pc.update(_frame(), [_big()]) == 0
    assert pc.update(_frame(), [_big()]) == 1
    assert len(s.captures) == 1
    assert len(s.captures[0]) == 1


def test_no_double_count_while_present():
    s = FakeSession()
    pc = PresenceCounter(s, present_frames=2, absent_frames=2)
    pc.update(_frame(), [_big()])
    pc.update(_frame(), [_big()])
    for _ in range(5):
        pc.update(_frame(), [_big()])
    assert pc.update(_frame(), [_big()]) == 1
    assert len(s.captures) == 1


def test_reentry_counts_again_after_clearance():
    s = FakeSession()
    pc = PresenceCounter(s, present_frames=2, absent_frames=2)
    pc.update(_frame(), [_big()])
    pc.update(_frame(), [_big()])
    pc.update(_frame(), [])
    pc.update(_frame(), [])
    pc.update(_frame(), [_big()])
    assert pc.update(_frame(), [_big()]) == 2
    assert len(s.captures) == 2


def test_flicker_below_debounce_does_not_count():
    s = FakeSession()
    pc = PresenceCounter(s, present_frames=3, absent_frames=2)
    pc.update(_frame(), [_big()])
    pc.update(_frame(), [])
    pc.update(_frame(), [_big()])
    assert pc.update(_frame(), []) == 0
    assert s.captures == []


def test_tiny_detection_filtered_out():
    s = FakeSession()
    pc = PresenceCounter(s, present_frames=1, absent_frames=2, min_area_frac=0.05)
    tiny = Detection(0, 0, 5, 5, "o", 0.9)
    assert pc.update(_frame(), [tiny]) == 0
    assert s.captures == []


def test_best_frame_is_highest_confidence():
    s = FakeSession()
    pc = PresenceCounter(s, present_frames=3, absent_frames=2)
    pc.update(_frame(), [_big(0.5)])
    pc.update(_frame(), [_big(0.95)])
    pc.update(_frame(), [_big(0.6)])
    assert abs(s.captures[0][0].confidence - 0.95) < 1e-6
