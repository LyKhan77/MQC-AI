import time

import numpy as np

import app.services.frame_grabber as fg


class FakeCapture:
    def __init__(self, frames, opened=True):
        self._frames = list(frames)
        self._opened = opened

    def isOpened(self):
        return self._opened

    def read(self):
        if self._frames:
            return True, self._frames.pop(0)
        return False, None

    def release(self):
        pass


def test_grabber_exposes_latest_frame():
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    g = fg.FrameGrabber("x", capture_factory=lambda src: FakeCapture([frame, frame]))
    g.start()
    try:
        got = None
        for _ in range(50):
            got = g.read()
            if got is not None:
                break
            time.sleep(0.01)
        assert got is not None
        assert got.shape == (4, 4, 3)
    finally:
        g.stop()


def test_grabber_finished_when_source_unopened():
    g = fg.FrameGrabber("x", capture_factory=lambda src: FakeCapture([], opened=False))
    g.start()
    for _ in range(50):
        if g.finished():
            break
        time.sleep(0.01)
    assert g.finished() is True
    assert g.read() is None
