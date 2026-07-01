import os

from PIL import Image as PILImage


def _make_crops(folder):
    os.makedirs(folder, exist_ok=True)
    for name in ["weld_0001.jpg", "weld_0002.jpg", "clean_0003.jpg"]:
        PILImage.new("RGB", (1280, 960), (50, 50, 50)).save(os.path.join(folder, name))
    return folder


def _submit(client, folder, name="B", camera_id=None):
    return client.post("/api/batches", json={"batch_name": name, "source_path": folder,
                                             "camera_id": camera_id}).json()["batch_id"]


def _submit_and_run(client, folder, name="B"):
    batch_id = _submit(client, folder, name)
    # TestClient runs the background task synchronously, so this returns terminal.
    client.post(f"/api/batches/{batch_id}/run", json={})
    return batch_id


def test_submit_creates_pending_batch_without_processing(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))

    resp = client.post("/api/batches", json={"batch_name": "Shift 1",
                                             "source_path": folder,
                                             "camera_id": "cam-01"})
    assert resp.status_code == 201
    batch_id = resp.json()["batch_id"]
    assert resp.json()["job_id"]

    status = client.get(f"/api/batches/{batch_id}/status").json()
    assert status["status"] == "pending"
    images = client.get(f"/api/batches/{batch_id}").json()["images"]
    assert len(images) == 3
    assert all(im["status"] == "pending" and im["defects"] == [] for im in images)


def test_run_processes_and_returns_result(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = _submit(client, folder, "Shift 1", camera_id="cam-01")

    run = client.post(f"/api/batches/{batch_id}/run", json={})
    assert run.status_code == 200

    status = client.get(f"/api/batches/{batch_id}/status").json()
    assert status["status"] == "done"
    assert status["progress"]["total"] == 3

    result = client.get(f"/api/batches/{batch_id}").json()
    assert result["batch_name"] == "Shift 1"
    assert len(result["images"]) == 3
    clean = next(i for i in result["images"] if i["filename"] == "clean_0003.jpg")
    assert clean["status"] == "clean"
    assert clean["defects"] == []


def test_rerun_allowed_after_done(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = _submit_and_run(client, folder, "Rerun")
    assert client.get(f"/api/batches/{batch_id}/status").json()["status"] == "done"
    second = client.post(f"/api/batches/{batch_id}/run", json={})
    assert second.status_code == 200
    assert client.get(f"/api/batches/{batch_id}/status").json()["status"] == "done"
    assert len(client.get(f"/api/batches/{batch_id}").json()["images"]) == 3


def test_reset_returns_batch_to_pending_raw(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = _submit_and_run(client, folder, "Reset")
    resp = client.post(f"/api/batches/{batch_id}/reset", json={})
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"
    images = client.get(f"/api/batches/{batch_id}").json()["images"]
    assert len(images) == 3
    assert all(im["status"] == "pending" and im["defects"] == [] for im in images)


def test_run_missing_batch_404(client):
    assert client.post("/api/batches/nope/run", json={}).status_code == 404


def test_run_records_confidence_override(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = _submit(client, folder, "Conf")
    client.post(f"/api/batches/{batch_id}/run", json={"confidence_threshold": 0.9})
    row = next(b for b in client.get("/api/batches").json() if b["id"] == batch_id)
    assert row["model_info"]["confidence"] == 0.9


def test_list_and_patch_batch(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = _submit_and_run(client, folder, "Shift 2")

    listed = client.get("/api/batches").json()
    assert any(b["id"] == batch_id for b in listed)

    patched = client.patch(f"/api/batches/{batch_id}",
                           json={"status": "reviewed",
                                 "reviewer": "inspector@gspemail.com"}).json()
    assert patched["status"] == "reviewed"
    assert patched["reviewer"] == "inspector@gspemail.com"


def test_patch_image_reviewed(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = _submit_and_run(client, folder, "S3")
    images = client.get(f"/api/batches/{batch_id}").json()["images"]
    image_id = images[0]["id"]

    patched = client.patch(f"/api/batches/{batch_id}/images/{image_id}",
                           json={"reviewed": True}).json()
    assert patched["reviewed"] is True


def test_delete_image_removes_row_and_file(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = _submit(client, folder, "Del")
    images = client.get(f"/api/batches/{batch_id}").json()["images"]
    target = images[0]
    file_path = os.path.join(folder, target["filename"])
    assert os.path.exists(file_path)

    resp = client.delete(f"/api/batches/{batch_id}/images/{target['id']}")
    assert resp.status_code == 200
    assert not os.path.exists(file_path)
    remaining = client.get(f"/api/batches/{batch_id}").json()["images"]
    assert len(remaining) == len(images) - 1
    row = next(b for b in client.get("/api/batches").json() if b["id"] == batch_id)
    assert row["image_count"] == len(images) - 1


def test_delete_image_404(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = _submit(client, folder, "Del2")
    assert client.delete(f"/api/batches/{batch_id}/images/nope").status_code == 404


def test_list_batches_includes_reviewed_count(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = _submit_and_run(client, folder, "RC")
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
