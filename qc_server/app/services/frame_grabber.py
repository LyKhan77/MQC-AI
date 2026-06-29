import threading

from .streaming import open_capture


class FrameGrabber:
    def __init__(self, source, capture_factory=open_capture):
        self._source = source
        self._capture_factory = capture_factory
        self._latest = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._finished = False
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def _loop(self):
        cap = self._capture_factory(self._source)
        try:
            if not cap.isOpened():
                return
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    break
                with self._lock:
                    self._latest = frame
        finally:
            cap.release()
            self._finished = True

    def read(self):
        with self._lock:
            if self._latest is None:
                return None
            return self._latest.copy()

    def finished(self):
        return self._finished

    def stop(self):
        self._stop.set()
