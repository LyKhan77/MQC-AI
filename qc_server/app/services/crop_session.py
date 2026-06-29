import os
from datetime import datetime, timezone

from ..config import settings
from .crop import crop_objects


class CropSession:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.session_ts = None
        self.folder = None
        self._single = None
        self._seen_ids = set()
        self._count = 0
        self._files = []

    def start(self):
        self.session_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")
        self.folder = os.path.join(settings.data_dir, "crops", self.camera_id, self.session_ts)
        self._single = None
        self._seen_ids = set()
        self._count = 0
        self._files = []

    def add_clean_frame(self, frame, detections, scale=1.0):
        if self.folder is None:
            return
        self._single = (frame.copy(), list(detections), scale)

    def add_tracked(self, frame, detections, scale=1.0):
        if self.folder is None:
            return
        new = [d for d in detections if d.track_id is not None and d.track_id not in self._seen_ids]
        for d in new:
            self._seen_ids.add(d.track_id)
        if not new:
            return
        written = crop_objects(frame, new, self.folder, scale=scale, start_index=self._count)
        self._files.extend(written)
        self._count += len(written)

    def finalize(self):
        if self.folder is None:
            return {"folder": None, "session_ts": None, "count": 0, "files": []}
        if self._single is not None:
            frame, dets, scale = self._single
            self._files = crop_objects(frame, dets, self.folder, scale=scale)
            self._count = len(self._files)
            self._single = None
        return {
            "folder": self.folder,
            "session_ts": self.session_ts,
            "count": self._count,
            "files": list(self._files),
        }

    def clear(self):
        self._single = None
        self._seen_ids = set()
        self._count = 0
        self._files = []


_sessions: dict[str, CropSession] = {}


def get_session(camera_id):
    s = _sessions.get(camera_id)
    if s is None:
        s = CropSession(camera_id)
        _sessions[camera_id] = s
    return s


def reset_session(camera_id):
    s = get_session(camera_id)
    s.start()
    return s
