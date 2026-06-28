import os
import tempfile

_TMP = tempfile.mkdtemp()
os.environ.setdefault("MQC_DATABASE_URL", f"sqlite:///{_TMP}/test.db")
os.environ.setdefault("MQC_DATA_DIR", _TMP)
os.environ.setdefault("MQC_CAMERA_MONITOR_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app import models  # noqa: F401  (register tables on Base)
from app.main import app


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
