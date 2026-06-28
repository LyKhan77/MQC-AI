import threading

from ..models import Camera
from .streaming import probe


def poll_once(db, probe_fn=probe) -> None:
    for cam in db.query(Camera).all():
        status = "online" if probe_fn(cam.source) else "offline"
        if cam.status != status:
            cam.status = status
    db.commit()


def start_monitor(session_factory, interval, stop_event) -> threading.Thread:
    def loop():
        while not stop_event.is_set():
            db = session_factory()
            try:
                poll_once(db)
            except Exception:
                pass
            finally:
                db.close()
            stop_event.wait(interval)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread
