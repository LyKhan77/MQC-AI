def _new_camera(**over):
    base = {
        "id": "cam-99", "name": "New", "type": "usb", "source": "/dev/video1",
        "location": "Lab", "status": "online", "resolution": "640x480",
        "fps": 30, "count_mode": "tracking",
    }
    base.update(over)
    return base


def test_create_and_get_camera(client):
    resp = client.post("/api/cameras", json=_new_camera())
    assert resp.status_code == 201
    assert resp.json()["id"] == "cam-99"

    listed = client.get("/api/cameras").json()
    assert any(c["id"] == "cam-99" and c["count_mode"] == "tracking" for c in listed)


def test_patch_camera(client):
    client.post("/api/cameras", json=_new_camera())
    resp = client.patch("/api/cameras/cam-99", json={"location": "Line A"})
    assert resp.status_code == 200
    assert resp.json()["location"] == "Line A"


def test_delete_camera(client):
    client.post("/api/cameras", json=_new_camera())
    assert client.delete("/api/cameras/cam-99").status_code == 200
    assert all(c["id"] != "cam-99" for c in client.get("/api/cameras").json())
