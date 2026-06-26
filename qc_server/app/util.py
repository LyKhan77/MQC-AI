from datetime import datetime, timezone
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"
