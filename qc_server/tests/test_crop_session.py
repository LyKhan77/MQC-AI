import os

import numpy as np

from app.services.crop_session import CropSession, get_session, reset_session
from app.services.object_detection import Detection


def _frame():
    return np.full((100, 100, 3), 128, dtype=np.uint8)


def test_capture_crops_all_detections(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = CropSession("cam-1")
    s.start()
    written = s.add_captured(_frame(), [Detection(10, 10, 40, 40, "o", 0.9),
                                        Detection(50, 50, 90, 90, "o", 0.8)])
    assert len(written) == 2
    assert s.finalize()["count"] == 2


def test_multiple_captures_accumulate(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = CropSession("cam-2")
    s.start()
    s.add_captured(_frame(), [Detection(10, 10, 40, 40, "o", 0.9)])
    s.add_captured(_frame(), [Detection(20, 20, 60, 60, "o", 0.9)])
    out = s.finalize()
    assert out["count"] == 2
    assert sorted(out["files"]) == ["obj_000.jpg", "obj_001.jpg"]


def test_tracking_mode_dedupes_by_track_id(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = CropSession("cam-3")
    s.start()
    d1 = Detection(10, 10, 40, 40, "o", 0.9); d1.track_id = 1
    d2 = Detection(50, 50, 90, 90, "o", 0.8); d2.track_id = 2
    s.add_tracked(_frame(), [d1])
    s.add_tracked(_frame(), [d1, d2])
    assert s.finalize()["count"] == 2


def test_approve_copies_only_selected(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = CropSession("cam-4")
    s.start()
    s.add_captured(_frame(), [Detection(10, 10, 40, 40, "o", 0.9),
                              Detection(50, 50, 90, 90, "o", 0.8)])
    files = s.finalize()["files"]
    approved = s.approve([files[0]])
    assert os.path.isdir(approved)
    assert os.listdir(approved) == [files[0]]


def test_start_resets_buffer(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = CropSession("cam-5")
    s.start()
    s.add_captured(_frame(), [Detection(10, 10, 40, 40, "o", 0.9)])
    s.start()
    assert s.finalize()["count"] == 0


def test_finalize_without_start_returns_empty():
    assert CropSession("cam-6").finalize() == {
        "folder": None, "session_ts": None, "count": 0, "files": []
    }


def test_registry_reset_returns_started_session(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = reset_session("cam-7")
    assert s.session_ts is not None
    assert get_session("cam-7") is s
