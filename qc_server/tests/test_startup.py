from sqlalchemy import inspect

from app.database import engine


def test_tables_created_on_startup(client):
    # entering the client fixture triggers app startup
    names = set(inspect(engine).get_table_names())
    assert {"cameras", "defect_classes", "settings", "audit_logs",
            "batches", "images", "defects"} <= names
