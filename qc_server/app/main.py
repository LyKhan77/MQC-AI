import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import (
    audit,
    batches,
    cameras,
    defect_classes,
    detect,
    images,
    models as models_router,
    settings as settings_router,
)

app = FastAPI(title="MQC-AI qc_server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    os.makedirs(os.path.join(settings.data_dir, "batches"), exist_ok=True)
    from . import models  # noqa: F401
    from .database import SessionLocal, ensure_active_model_column, ensure_column
    from .services.seed import seed_if_empty
    Base.metadata.create_all(engine)
    ensure_active_model_column(engine)
    ensure_column(engine, "settings", "input_mode_enabled", "BOOLEAN DEFAULT 1")
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    if settings.camera_monitor_enabled:
        import threading
        from .database import SessionLocal as _SessionLocal
        from .services.camera_monitor import start_monitor
        app.state.camera_monitor_stop = threading.Event()
        start_monitor(_SessionLocal, settings.camera_poll_interval, app.state.camera_monitor_stop)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(cameras.router)
app.include_router(defect_classes.router)
app.include_router(models_router.router)
app.include_router(detect.router)
app.include_router(settings_router.router)
app.include_router(audit.router)
app.include_router(batches.router)
app.include_router(images.router)
