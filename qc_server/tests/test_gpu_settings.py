def test_gpu_inventory_endpoint(client, monkeypatch):
    from app.routers import system

    monkeypatch.setattr(
        system,
        "get_gpu_inventory",
        lambda: {
            "available": True,
            "gpus": [{
                "index": 0,
                "name": "RTX 4090",
                "memory_total_mb": 24564,
                "memory_used_mb": 563,
                "memory_free_mb": 24001,
                "utilization_percent": 0,
            }],
            "error": None,
        },
    )

    body = client.get("/api/system/gpus").json()
    assert body["available"] is True
    assert body["gpus"][0]["index"] == 0
    assert body["gpus"][0]["memory_free_mb"] == 24001


def test_settings_roundtrip_task_devices(client, monkeypatch):
    from app.routers import settings as settings_router

    monkeypatch.setattr(
        settings_router.gpu_service,
        "get_gpu_inventory",
        lambda: {"available": True, "gpus": [{"index": 0}, {"index": 1}], "error": None},
    )

    response = client.put("/api/settings", json={
        "object_detection_device": "0",
        "qc_device": "1",
        "quantity_device": "auto",
    })

    assert response.status_code == 200
    body = response.json()
    assert body["object_detection_device"] == "0"
    assert body["qc_device"] == "1"
    assert body["quantity_device"] == "auto"


def test_settings_rejects_unknown_gpu_index(client, monkeypatch):
    from app.routers import settings as settings_router

    monkeypatch.setattr(
        settings_router.gpu_service,
        "get_gpu_inventory",
        lambda: {"available": True, "gpus": [{"index": 0}], "error": None},
    )

    response = client.put("/api/settings", json={"qc_device": "9"})

    assert response.status_code == 400
    assert "GPU index 9" in response.json()["detail"]
