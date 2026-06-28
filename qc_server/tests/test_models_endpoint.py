import app.routers.models as models_router


def test_list_models_lists_pt_files(client, tmp_path, monkeypatch):
    (tmp_path / "metal.pt").write_bytes(b"x")
    (tmp_path / "weld.pt").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("ignore")
    monkeypatch.setattr(models_router.app_settings, "models_dir", str(tmp_path))

    data = client.get("/api/models").json()
    assert data["models"] == ["metal.pt", "weld.pt"]
    assert "active" in data


def test_put_settings_persists_active_model(client):
    client.put("/api/settings", json={"active_model": "metal.pt"})
    assert client.get("/api/settings").json()["active_model"] == "metal.pt"
