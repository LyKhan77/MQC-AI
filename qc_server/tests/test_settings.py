def test_get_settings_defaults(client):
    data = client.get("/api/settings").json()
    assert data["defect_strategy"] == "mock"
    assert data["confidence_threshold"] == 0.5


def test_put_settings(client):
    resp = client.put("/api/settings", json={"confidence_threshold": 0.7,
                                             "defect_strategy": "sam3_prompt"})
    assert resp.status_code == 200
    assert resp.json()["confidence_threshold"] == 0.7
    assert resp.json()["defect_strategy"] == "sam3_prompt"
    # persisted
    assert client.get("/api/settings").json()["defect_strategy"] == "sam3_prompt"
