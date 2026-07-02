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
