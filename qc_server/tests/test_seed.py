from app.database import SessionLocal
from app.models import DefectClass
from app.services.seed import seed_if_empty


def test_seed_runs_on_startup(client):
    cams = client.get("/api/cameras").json()
    assert len(cams) >= 3
    classes = {c["name"] for c in client.get("/api/defect-classes").json()}
    assert {"scratch", "porosity", "crack", "undercut", "lack of fusion"} <= classes
    assert len(classes) >= 20
    assert client.get("/api/settings").json()["defect_strategy"] == "mock"


def test_seed_adds_missing_classes_without_overwriting_existing():
    db = SessionLocal()
    try:
        db.add(DefectClass(id="dc-scratch", name="user scratch", category="custom", color="#000000", enabled=False))
        db.commit()

        seed_if_empty(db)

        scratch = db.get(DefectClass, "dc-scratch")
        assert scratch.name == "user scratch"
        assert scratch.category == "custom"
        assert scratch.enabled is False
        assert db.get(DefectClass, "dc-lack-of-fusion") is not None
    finally:
        db.close()
