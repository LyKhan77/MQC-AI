import os

from PIL import Image as PILImage


def _make_crops(folder):
    os.makedirs(folder, exist_ok=True)
    for name in ["weld_0001.jpg", "clean_0002.jpg"]:
        PILImage.new("RGB", (320, 240), (10, 20, 30)).save(os.path.join(folder, name))
    return folder


def test_serve_image_file(client, tmp_path):
    folder = _make_crops(str(tmp_path / "crops"))
    batch_id = client.post("/api/batches", json={"batch_name": "S",
                                                 "source_path": folder}).json()["batch_id"]
    image = client.get(f"/api/batches/{batch_id}").json()["images"][0]

    resp = client.get(image["url"])
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")
    assert len(resp.content) > 0


def test_serve_missing_image_404(client):
    assert client.get("/api/images/img_doesnotexist/file").status_code == 404
