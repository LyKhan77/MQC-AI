import os

from PIL import Image as PILImage


def _make_crops(folder):
    os.makedirs(folder, exist_ok=True)
    for name in ["weld_0001.jpg", "weld_0002.jpg", "clean_0003.jpg"]:
        PILImage.new("RGB", (1280, 960), (50, 50, 50)).save(os.path.join(folder, name))
    return folder


def test_submit_batch_processes_and_returns_result(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))

    resp = client.post("/api/batches", json={"batch_name": "Shift 1",
                                             "source_path": folder,
                                             "camera_id": "cam-01"})
    assert resp.status_code == 201
    batch_id = resp.json()["batch_id"]
    assert resp.json()["job_id"]

    # TestClient runs the background task before returning, so status is terminal
    status = client.get(f"/api/batches/{batch_id}/status").json()
    assert status["status"] == "done"
    assert status["progress"]["total"] == 3

    result = client.get(f"/api/batches/{batch_id}").json()
    assert result["batch_name"] == "Shift 1"
    assert len(result["images"]) == 3
    clean = next(i for i in result["images"] if i["filename"] == "clean_0003.jpg")
    assert clean["status"] == "clean"
    assert clean["defects"] == []


def test_list_and_patch_batch(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = client.post("/api/batches", json={"batch_name": "Shift 2",
                                                 "source_path": folder}).json()["batch_id"]

    listed = client.get("/api/batches").json()
    assert any(b["id"] == batch_id for b in listed)

    patched = client.patch(f"/api/batches/{batch_id}",
                           json={"status": "reviewed",
                                 "reviewer": "inspector@gspemail.com"}).json()
    assert patched["status"] == "reviewed"
    assert patched["reviewer"] == "inspector@gspemail.com"


def test_patch_image_reviewed(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = client.post("/api/batches", json={"batch_name": "S3",
                                                 "source_path": folder}).json()["batch_id"]
    images = client.get(f"/api/batches/{batch_id}").json()["images"]
    image_id = images[0]["id"]

    patched = client.patch(f"/api/batches/{batch_id}/images/{image_id}",
                           json={"reviewed": True}).json()
    assert patched["reviewed"] is True


def test_list_batches_includes_reviewed_count(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = client.post("/api/batches", json={"batch_name": "RC",
                                                 "source_path": folder}).json()["batch_id"]
    images = client.get(f"/api/batches/{batch_id}").json()["images"]
    client.patch(f"/api/batches/{batch_id}/images/{images[0]['id']}", json={"reviewed": True})

    row = next(b for b in client.get("/api/batches").json() if b["id"] == batch_id)
    assert row["image_count"] == 3
    assert row["reviewed_count"] == 1


def test_delete_batch_removes_it(client, tmp_path):
    src = tmp_path / "crops"
    src.mkdir()
    created = client.post(
        "/api/batches",
        json={"batch_name": "todelete", "source_path": str(src), "camera_id": None},
    ).json()
    batch_id = created["batch_id"]

    assert client.delete(f"/api/batches/{batch_id}").status_code == 200
    assert client.get(f"/api/batches/{batch_id}").status_code == 404


def test_delete_missing_batch_404(client):
    assert client.delete("/api/batches/nope").status_code == 404
