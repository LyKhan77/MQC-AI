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


def test_annotated_mjpeg_yields_and_reports_count(monkeypatch):
    monkeypatch.setattr(
        ann,
        "detect",
        lambda frame, conf, model_path: [Detection(0, 0, 5, 5, "x", 0.9)],
    )
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    counts = []
    chunks = list(
        ann.annotated_mjpeg(FakeGrabber([frame]), "single", 0.5, "m.pt", counts.append)
    )
    assert len(chunks) >= 1
    assert b"image/jpeg" in chunks[0]
    assert counts == [1]
