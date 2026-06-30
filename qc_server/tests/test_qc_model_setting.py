def test_qc_model_defaults_empty(client):
    assert client.get("/api/settings").json()["qc_model"] == ""


def test_put_qc_model_persists(client):
    resp = client.put("/api/settings", json={"qc_model": "sam3.pt"})
    assert resp.status_code == 200
    assert resp.json()["qc_model"] == "sam3.pt"
    assert client.get("/api/settings").json()["qc_model"] == "sam3.pt"


def test_qc_confidence_defaults_and_persists(client):
    assert client.get("/api/settings").json()["qc_confidence_threshold"] == 0.5
    client.put("/api/settings", json={"qc_confidence_threshold": 0.3})
    assert client.get("/api/settings").json()["qc_confidence_threshold"] == 0.3
