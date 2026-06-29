import numpy as np

from app.services.crop_session import CropSession, get_session, reset_session
from app.services.object_detection import Detection


def _frame():
    return np.full((100, 100, 3), 128, dtype=np.uint8)


def test_single_mode_crops_on_finalize(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = CropSession("cam-1")
    s.start()
    dets = [Detection(10, 10, 40, 40, "o", 0.9), Detection(50, 50, 90, 90, "o", 0.8)]
    s.add_clean_frame(_frame(), dets)
    out = s.finalize()
    assert out["count"] == 2
    assert len(out["files"]) == 2


def test_tracking_mode_dedupes_by_track_id(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = CropSession("cam-2")
    s.start()
    d1 = Detection(10, 10, 40, 40, "o", 0.9); d1.track_id = 1
    d2 = Detection(50, 50, 90, 90, "o", 0.8); d2.track_id = 2
    s.add_tracked(_frame(), [d1])          # new id 1
    s.add_tracked(_frame(), [d1, d2])      # id 1 repeats, id 2 new
    out = s.finalize()
    assert out["count"] == 2               # one crop per unique track_id


def test_start_resets_buffer(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = CropSession("cam-3")
    s.start()
    d = Detection(10, 10, 40, 40, "o", 0.9); d.track_id = 1
    s.add_tracked(_frame(), [d])
    s.start()                              # restart discards prior run
    assert s.finalize()["count"] == 0


def test_finalize_without_start_returns_empty():
    s = CropSession("cam-4")
    out = s.finalize()
    assert out == {"folder": None, "session_ts": None, "count": 0, "files": []}


def test_registry_reset_returns_started_session(tmp_path, monkeypatch):
    import app.services.crop_session as cs
    monkeypatch.setattr(cs.settings, "data_dir", str(tmp_path))
    s = reset_session("cam-5")
    assert s.session_ts is not None
    assert get_session("cam-5") is s
