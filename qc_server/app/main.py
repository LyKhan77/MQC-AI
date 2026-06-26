import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import audit, cameras, defect_classes, settings as settings_router

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
    from . import models  # noqa: F401  (register tables)
    Base.metadata.create_all(engine)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(cameras.router)
app.include_router(defect_classes.router)
app.include_router(settings_router.router)
app.include_router(audit.router)
