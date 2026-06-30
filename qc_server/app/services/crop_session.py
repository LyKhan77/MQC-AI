import os
import shutil
from datetime import datetime, timezone

from ..config import settings
from .crop import crop_objects


class CropSession:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.session_ts = None
        self.folder = None
        self._seen_ids = set()
        self._count = 0
        self._files = []

    def start(self):
        self.session_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S")
        self.folder = os.path.join(settings.data_dir, "crops", self.camera_id, self.session_ts)
        self._seen_ids = set()
        self._count = 0
        self._files = []

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

    def add_captured(self, frame, detections, scale=1.0):
        if self.folder is None:
            return []
        written = crop_objects(frame, detections, self.folder, scale=scale, start_index=self._count)
        self._files.extend(written)
        self._count += len(written)
        return written

    def finalize(self):
        if self.folder is None:
            return {"folder": None, "session_ts": None, "count": 0, "files": []}
        return {
            "folder": self.folder,
            "session_ts": self.session_ts,
            "count": self._count,
            "files": list(self._files),
        }

    def approve(self, selected_files):
        if self.folder is None:
            return None
        approved = os.path.join(self.folder, "approved")
        os.makedirs(approved, exist_ok=True)
        copied = 0
        for name in selected_files:
            src = os.path.join(self.folder, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(approved, name))
                copied += 1
        return approved if copied else None

    def clear(self):
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


def approve_session(key, files):
    return get_session(key).approve(files)


def crop_file_path(key, session_ts, filename):
    return os.path.join(settings.data_dir, "crops", key, session_ts, filename)
