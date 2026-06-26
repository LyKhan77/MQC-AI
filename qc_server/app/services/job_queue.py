from threading import Lock

_PROGRESS: dict[str, dict] = {}
_LOCK = Lock()


def set_total(batch_id: str, total: int) -> None:
    with _LOCK:
        _PROGRESS[batch_id] = {"done": 0, "total": total}


def increment(batch_id: str) -> None:
    with _LOCK:
        if batch_id in _PROGRESS:
            _PROGRESS[batch_id]["done"] += 1


def get(batch_id: str) -> dict:
    with _LOCK:
        return dict(_PROGRESS.get(batch_id, {"done": 0, "total": 0}))
