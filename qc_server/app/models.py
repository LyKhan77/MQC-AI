from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Camera(Base):
    __tablename__ = "cameras"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="offline")
    resolution: Mapped[str] = mapped_column(String, default="")
    fps: Mapped[int] = mapped_column(Integer, default=0)
    count_mode: Mapped[str] = mapped_column(String, default="single")


class DefectClass(Base):
    __tablename__ = "defect_classes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    color: Mapped[str] = mapped_column(String, default="#da1e28")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Setting(Base):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.5)
    detection_model: Mapped[str] = mapped_column(String, default="YOLOv8n")
    segmentation_model: Mapped[str] = mapped_column(String, default="SAM3")
    defect_strategy: Mapped[str] = mapped_column(String, default="mock")
    active_model: Mapped[str] = mapped_column(String, default="")
    input_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    qc_model: Mapped[str] = mapped_column(String, default="")
    qc_confidence_threshold: Mapped[float] = mapped_column(Float, default=0.5)
    quantity_model: Mapped[str] = mapped_column(String, default="")
    quantity_confidence_threshold: Mapped[float] = mapped_column(Float, default=0.5)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[str] = mapped_column(String)
    user: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    detail: Mapped[str] = mapped_column(String, default="")


class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    source_path: Mapped[str] = mapped_column(String)
    camera_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    defect_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="processing")
    reviewer: Mapped[str | None] = mapped_column(String, nullable=True)
    model_info: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(String, nullable=True)


class Image(Base):
    __tablename__ = "images"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    batch_id: Mapped[str] = mapped_column(ForeignKey("batches.id"))
    filename: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="clean")
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    defects: Mapped[list["Defect"]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )


class Defect(Base):
    __tablename__ = "defects"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.id"))
    type: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    polygon: Mapped[list] = mapped_column(JSON)
    image: Mapped["Image"] = relationship(back_populates="defects")


class QuantityCheck(Base):
    __tablename__ = "quantity_checks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String, default="image")
    count_mode: Mapped[str] = mapped_column(String, default="static")
    input_summary: Mapped[str] = mapped_column(String, default="")
    model_used: Mapped[str] = mapped_column(String, default="")
    confidence_used: Mapped[float] = mapped_column(Float, default=0.5)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    per_class_counts: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_per_class: Mapped[dict] = mapped_column(JSON, default=dict)
    inputs: Mapped[list] = mapped_column(JSON, default=list)
    tolerance: Mapped[int] = mapped_column(Integer, default=0)
    verdict: Mapped[str] = mapped_column(String, default="none")
    reviewer: Mapped[str] = mapped_column(String, default="")
    notes: Mapped[str] = mapped_column(String, default="")
