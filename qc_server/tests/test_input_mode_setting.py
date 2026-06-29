from sqlalchemy import create_engine, inspect, text

from app import database


def test_ensure_column_adds_then_idempotent(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path}/m.db")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE settings (id INTEGER PRIMARY KEY)"))
    database.ensure_column(eng, "settings", "input_mode_enabled", "BOOLEAN DEFAULT 1")
    cols = [c["name"] for c in inspect(eng).get_columns("settings")]
    assert "input_mode_enabled" in cols
    database.ensure_column(eng, "settings", "input_mode_enabled", "BOOLEAN DEFAULT 1")


def test_settings_exposes_input_mode_enabled(client):
    assert client.get("/api/settings").json()["input_mode_enabled"] is True
    client.put("/api/settings", json={"input_mode_enabled": False})
    assert client.get("/api/settings").json()["input_mode_enabled"] is False
