import numpy as np

import app.services.detect_extract as dx
from app.services.object_detection import Detection


class FakeCap:
    def __init__(self, frames):
        self._frames = list(frames)

    def get(self, prop):
        return len(self._frames)

    def read(self):
        if self._frames:
            return True, self._frames.pop(0)
        return False, None

    def release(self):
        pass


def _frame():
    return np.zeros((100, 100, 3), dtype=np.uint8)


def test_run_video_extract_counts_one_object(tmp_path, monkeypatch):
    import app.services.crop_session as cs

    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    big = Detection(10, 10, 60, 60, "o", 0.9)
    frames = [_frame() for _ in range(4)] + [_frame() for _ in range(3)]
    seq = [[big]] * 4 + [[]] * 3
    calls = {"i": 0}

    def fake_detect(frame, conf, model_path):
        d = seq[calls["i"]]
        calls["i"] += 1
        return d

    monkeypatch.setattr(dx, "detect", fake_detect)
    dx.start("vid-1")
    dx.run_video_extract(
        "vid-1",
        "x.mp4",
        0.5,
        "m.pt",
        960,
        capture_factory=lambda p: FakeCap(frames),
    )
    st = dx.status("vid-1")
    assert st["status"] == "done"
    assert st["count"] == 1
