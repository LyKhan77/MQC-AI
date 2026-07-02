import os

from app.config import settings as app_settings


def _seed_tmp_crop(crop_key):
    d = os.path.join(app_settings.data_dir, "quantity", "_tmp", crop_key)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "obj_000.png"), "wb") as f:
        f.write(b"\x89PNG\r\n")
    return d


def test_create_and_list_check(client):
    payload = {
        "source_type": "image",
        "count_mode": "static",
        "input_summary": "2 images",
        "model_used": "count.pt",
        "confidence_used": 0.6,
        "total_count": 20,
        "per_class_counts": {"bolt": 12, "nut": 8},
        "expected_total": 20,
        "expected_per_class": {"bolt": 12, "nut": 8},
        "tolerance": 0,
        "verdict": "pass",
        "reviewer": "inspector@gspemail.com",
        "notes": "",
    }
    created = client.post("/api/quantity/checks", json=payload)
    assert created.status_code == 201
    cid = created.json()["id"]
    assert created.json()["verdict"] == "pass"
    assert created.json()["per_class_counts"] == {"bolt": 12, "nut": 8}

    listed = client.get("/api/quantity/checks").json()
    assert any(c["id"] == cid for c in listed)

    got = client.get(f"/api/quantity/checks/{cid}")
    assert got.status_code == 200
    assert got.json()["total_count"] == 20

    missing = client.get("/api/quantity/checks/nope")
    assert missing.status_code == 404


def test_inputs_persist_and_delete(client):
    payload = {
        "total_count": 5,
        "per_class_counts": {"a": 5},
        "verdict": "none",
        "inputs": [
            {"name": "a.png", "total": 3, "per_class": {"a": 3}},
            {"name": "b.png", "total": 2, "per_class": {"a": 2}},
        ],
    }
    created = client.post("/api/quantity/checks", json=payload)
    assert created.status_code == 201
    cid = created.json()["id"]
    assert created.json()["inputs"][0]["name"] == "a.png"

    deleted = client.delete(f"/api/quantity/checks/{cid}")
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": cid}
    assert client.get(f"/api/quantity/checks/{cid}").status_code == 404
    assert client.delete("/api/quantity/checks/nope").status_code == 404


def test_save_persists_crops_and_delete_removes(client):
    tmp = _seed_tmp_crop("k1")
    payload = {
        "total_count": 1,
        "per_class_counts": {"a": 1},
        "verdict": "none",
        "inputs": [
            {
                "name": "a.png",
                "total": 1,
                "per_class": {"a": 1},
                "crop_key": "k1",
                "crops": ["obj_000.png"],
            }
        ],
    }
    created = client.post("/api/quantity/checks", json=payload)
    assert created.status_code == 201
    cid = created.json()["id"]
    crops = created.json()["inputs"][0]["crops"]
    assert crops == [f"/api/quantity/crops/{cid}/0/obj_000.png"]
    assert "crop_key" not in created.json()["inputs"][0]
    assert not os.path.isdir(tmp)
    assert client.get(crops[0]).status_code == 200

    assert client.delete(f"/api/quantity/checks/{cid}").status_code == 200
    assert not os.path.isdir(os.path.join(app_settings.data_dir, "quantity", cid))


def test_save_rejects_crop_key_traversal(client):
    # A file outside the _tmp tree must never be moved via a crafted crop_key.
    secret = os.path.join(app_settings.data_dir, "secret.txt")
    with open(secret, "wb") as f:
        f.write(b"top-secret")
    payload = {
        "total_count": 1,
        "per_class_counts": {"a": 1},
        "verdict": "none",
        "inputs": [
            {
                "name": "a.png",
                "total": 1,
                "per_class": {"a": 1},
                "crop_key": "../..",
                "crops": ["secret.txt"],
            }
        ],
    }
    created = client.post("/api/quantity/checks", json=payload)
    assert created.status_code == 201
    assert os.path.isfile(secret)  # traversal rejected; file not moved
