import os

from PIL import Image as PILImage

from app.config import settings as app_settings
from app.database import SessionLocal
from app.models import Setting


def _batch_with_image(client, tmp_path):
    folder = tmp_path / "crops"
    folder.mkdir()
    PILImage.new("RGB", (100, 80), (50, 50, 50)).save(folder / "part.jpg")
    batch_id = client.post(
        "/api/batches",
        json={"batch_name": "SAM", "source_path": str(folder), "camera_id": None},
    ).json()["batch_id"]
    image = client.get(f"/api/batches/{batch_id}").json()["images"][0]
    return batch_id, image


def _set_qc_model(name="sam3.pt"):
    os.makedirs(app_settings.models_dir, exist_ok=True)
    open(os.path.join(app_settings.models_dir, name), "wb").close()
    db = SessionLocal()
    setting = db.get(Setting, 1)
    setting.qc_model = name
    db.commit()
    db.close()


def test_segment_point_returns_polygon(client, tmp_path, monkeypatch):
    from app.services.inference import sam_interactive

    batch_id, image = _batch_with_image(client, tmp_path)
    _set_qc_model()
    monkeypatch.setattr(
        sam_interactive,
        "segment",
        lambda *args, **kwargs: [[1, 2], [10, 2], [10, 9]],
    )

    resp = client.post(
        f"/api/batches/{batch_id}/images/{image['id']}/segment",
        json={"point": [5, 6]},
    )

    assert resp.status_code == 200
    assert resp.json() == {"polygon": [[1, 2], [10, 2], [10, 9]]}


def test_segment_box_returns_polygon(client, tmp_path, monkeypatch):
    from app.services.inference import sam_interactive

    batch_id, image = _batch_with_image(client, tmp_path)
    _set_qc_model()
    monkeypatch.setattr(
        sam_interactive,
        "segment",
        lambda *args, **kwargs: [[3, 4], [12, 4], [12, 11]],
    )

    resp = client.post(
        f"/api/batches/{batch_id}/images/{image['id']}/segment",
        json={"box": [1, 2, 20, 30]},
    )

    assert resp.status_code == 200
    assert resp.json()["polygon"] == [[3, 4], [12, 4], [12, 11]]


def test_segment_requires_exactly_one_prompt(client, tmp_path):
    batch_id, image = _batch_with_image(client, tmp_path)
    _set_qc_model()
    url = f"/api/batches/{batch_id}/images/{image['id']}/segment"

    assert client.post(url, json={}).status_code == 400
    assert client.post(url, json={"point": [1, 2], "box": [1, 2, 3, 4]}).status_code == 400


def test_segment_requires_qc_model(client, tmp_path):
    batch_id, image = _batch_with_image(client, tmp_path)

    resp = client.post(
        f"/api/batches/{batch_id}/images/{image['id']}/segment",
        json={"point": [5, 6]},
    )

    assert resp.status_code == 409


def test_segment_reuses_image_ownership_404(client, tmp_path):
    batch_id, image = _batch_with_image(client, tmp_path)
    _set_qc_model()

    assert client.post(
        f"/api/batches/nope/images/{image['id']}/segment",
        json={"point": [5, 6]},
    ).status_code == 404
    assert client.post(
        f"/api/batches/{batch_id}/images/nope/segment",
        json={"point": [5, 6]},
    ).status_code == 404
