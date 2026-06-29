import numpy as np

import app.services.annotated_stream as ann
from app.services.object_detection import Detection


class FakeGrabber:
    def __init__(self, frames):
        self._frames = list(frames)
        self._finished = False

    def read(self):
        if self._frames:
            return self._frames.pop(0)
        self._finished = True
        return None

    def finished(self):
        return self._finished


def test_annotate_draws_on_frame():
    frame = np.zeros((40, 40, 3), dtype=np.uint8)
    out = ann.annotate(frame, [Detection(2, 2, 20, 20, "x", 0.9)], 1)
    assert out.shape == (40, 40, 3)
    assert out.sum() > 0


def test_downscale_caps_width():
    frame = np.zeros((600, 1200, 3), dtype=np.uint8)
    out = ann.downscale(frame, 960)
    assert out.shape[1] == 960
    assert out.shape[0] == 480


def test_downscale_noop_when_small():
    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    assert ann.downscale(frame, 960).shape == (100, 200, 3)


def test_annotated_mjpeg_yields_and_reports_stats(monkeypatch):
    monkeypatch.setattr(
        ann,
        "detect",
        lambda frame, conf, model_path: [Detection(0, 0, 5, 5, "x", 0.9)],
    )
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    stats = []
    chunks = list(
        ann.annotated_mjpeg(
            FakeGrabber([frame]),
            "single",
            0.5,
            "m.pt",
            lambda count, fps: stats.append((count, fps)),
            max_width=960,
            max_fps=0,
        )
    )
    assert len(chunks) >= 1
    assert b"image/jpeg" in chunks[0]
    assert stats and stats[0][0] == 1
