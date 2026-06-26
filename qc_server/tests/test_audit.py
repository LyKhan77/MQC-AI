def test_post_and_list_audit(client):
    resp = client.post("/api/audit", json={"user": "inspector@gspemail.com",
                                           "action": "BATCH_LOADED",
                                           "detail": "Loaded shift1"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"]
    assert body["timestamp"]

    listed = client.get("/api/audit").json()
    assert listed[0]["action"] == "BATCH_LOADED"  # newest first
