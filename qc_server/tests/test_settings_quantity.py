def test_settings_roundtrip_quantity_fields(client):
    resp = client.put("/api/settings", json={
        "quantity_model": "count.pt",
        "quantity_confidence_threshold": 0.6,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["quantity_model"] == "count.pt"
    assert body["quantity_confidence_threshold"] == 0.6

    got = client.get("/api/settings").json()
    assert got["quantity_model"] == "count.pt"
    assert got["quantity_confidence_threshold"] == 0.6


def test_settings_roundtrip_quantity_nms(client):
    resp = client.put("/api/settings", json={
        "quantity_nms_iou": 0.4,
        "quantity_agnostic_nms": False,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["quantity_nms_iou"] == 0.4
    assert body["quantity_agnostic_nms"] is False
