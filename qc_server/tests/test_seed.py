def test_seed_runs_on_startup(client):
    cams = client.get("/api/cameras").json()
    assert len(cams) >= 3
    classes = {c["name"] for c in client.get("/api/defect-classes").json()}
    assert {"porosity", "spatter", "scratch", "color"} <= classes
    assert client.get("/api/settings").json()["defect_strategy"] == "mock"
