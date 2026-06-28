from collections.abc import Iterator

from sqlalchemy import create_engine, inspect as sa_inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_active_model_column(eng=engine) -> None:
    insp = sa_inspect(eng)
    if "settings" not in insp.get_table_names():
        return
    cols = [c["name"] for c in insp.get_columns("settings")]
    if "active_model" not in cols:
        with eng.begin() as conn:
            conn.execute(text("ALTER TABLE settings ADD COLUMN active_model VARCHAR DEFAULT ''"))
