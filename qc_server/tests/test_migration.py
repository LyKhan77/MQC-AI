from sqlalchemy import create_engine, inspect, text

from app.database import ensure_active_model_column, ensure_column


def test_ensure_active_model_column_adds_then_idempotent(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path}/m.db")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE settings (id INTEGER PRIMARY KEY)"))

    ensure_active_model_column(eng)
    cols = [c["name"] for c in inspect(eng).get_columns("settings")]
    assert "active_model" in cols

    ensure_active_model_column(eng)


def test_ensure_mask_polygon_column_adds_to_old_images_table(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path}/m.db")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE images (id VARCHAR PRIMARY KEY)"))

    ensure_column(eng, "images", "mask_polygon", "JSON")
    ensure_column(eng, "images", "mask_polygon", "JSON")

    cols = [c["name"] for c in inspect(eng).get_columns("images")]
    assert "mask_polygon" in cols
