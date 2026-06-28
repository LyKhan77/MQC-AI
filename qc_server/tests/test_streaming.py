import app.services.streaming as streaming


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


class FakeBuf:
    def __init__(self, data):
        self._data = data

    def tobytes(self):
        return self._data


def test_probe_true_when_frame_available(monkeypatch):
    monkeypatch.setattr(streaming, "open_capture", lambda src: FakeCapture(["frame"]))
    assert streaming.probe("rtsp://x") is True


def test_probe_false_when_not_opened(monkeypatch):
    monkeypatch.setattr(streaming, "open_capture", lambda src: FakeCapture([], opened=False))
    assert streaming.probe("rtsp://x") is False


def test_mjpeg_frames_yields_multipart_jpeg(monkeypatch):
    monkeypatch.setattr(streaming, "open_capture", lambda src: FakeCapture(["f1", "f2"]))
    monkeypatch.setattr(streaming.cv2, "imencode", lambda ext, frame: (True, FakeBuf(b"JPG")))
    chunks = list(streaming.mjpeg_frames("rtsp://x"))
    assert len(chunks) == 2
    assert b"Content-Type: image/jpeg" in chunks[0]
    assert b"JPG" in chunks[0]
