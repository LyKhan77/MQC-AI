def _new_class(**over):
    base = {"id": "dc-1", "name": "porosity", "category": "welding",
            "color": "#ff0000", "enabled": True}
    base.update(over)
    return base


def test_create_and_list_defect_class(client):
    assert client.post("/api/defect-classes", json=_new_class()).status_code == 201
    listed = client.get("/api/defect-classes").json()
    assert any(c["name"] == "porosity" for c in listed)


def test_create_auto_generates_id_from_name(client):
    resp = client.post("/api/defect-classes", json={"name": "custom flaw", "category": "coating"})
    assert resp.status_code == 201
    assert resp.json()["id"] == "dc-custom-flaw"


def test_create_auto_id_dedupes(client):
    client.post("/api/defect-classes", json={"name": "custom flaw", "category": "coating"})
    second = client.post("/api/defect-classes", json={"name": "custom flaw", "category": "coating"})
    assert second.json()["id"] == "dc-custom-flaw-2"


def test_patch_and_delete_defect_class(client):
    client.post("/api/defect-classes", json=_new_class())
    patched = client.patch("/api/defect-classes/dc-1", json={"enabled": False})
    assert patched.json()["enabled"] is False
    assert client.delete("/api/defect-classes/dc-1").status_code == 200
