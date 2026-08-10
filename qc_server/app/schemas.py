from pydantic import BaseModel, ConfigDict, Field


class CameraIn(BaseModel):
    id: str
    name: str
    type: str
    source: str
    location: str = ""
    status: str = "offline"
    resolution: str = ""
    fps: int = 0
    count_mode: str = "single"


class CameraOut(CameraIn):
    model_config = ConfigDict(from_attributes=True)


class DefectClassIn(BaseModel):
    id: str
    name: str
    category: str
    color: str = "#da1e28"
    enabled: bool = True


class DefectClassOut(DefectClassIn):
    model_config = ConfigDict(from_attributes=True)


class DefectClassCreate(BaseModel):
    id: str | None = None
    name: str
    category: str
    color: str = "#da1e28"
    enabled: bool = True


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    confidence_threshold: float
    detection_model: str
    segmentation_model: str
    defect_strategy: str
    active_model: str
    qc_model: str
    qc_confidence_threshold: float
    quantity_model: str
    quantity_confidence_threshold: float
    quantity_nms_iou: float
    quantity_agnostic_nms: bool
    quantity_classes: str
    input_mode_enabled: bool
    object_detection_device: str
    qc_device: str
    quantity_device: str


class SettingUpdate(BaseModel):
    confidence_threshold: float | None = None
    detection_model: str | None = None
    segmentation_model: str | None = None
    defect_strategy: str | None = None
    active_model: str | None = None
    qc_model: str | None = None
    qc_confidence_threshold: float | None = None
    quantity_model: str | None = None
    quantity_confidence_threshold: float | None = None
    quantity_nms_iou: float | None = None
    quantity_agnostic_nms: bool | None = None
    quantity_classes: str | None = None
    input_mode_enabled: bool | None = None
    object_detection_device: str | None = None
    qc_device: str | None = None
    quantity_device: str | None = None


class QuantityDetectOut(BaseModel):
    total: int
    per_class: dict
    detections: list
    width: int
    height: int
    crop_key: str
    crops: list
    frame_url: str | None = None


class AuditLogIn(BaseModel):
    user: str
    action: str
    detail: str = ""


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    timestamp: str
    user: str
    action: str
    detail: str


class BatchCreate(BaseModel):
    batch_name: str
    source_path: str
    camera_id: str | None = None


class BatchRunRequest(BaseModel):
    confidence_threshold: float | None = None


class BatchCreateResponse(BaseModel):
    batch_id: str
    job_id: str


class BatchStatusOut(BaseModel):
    batch_id: str
    status: str
    progress: dict


class BatchSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    source_path: str
    camera_id: str | None
    created_at: str
    image_count: int
    defect_count: int
    status: str
    reviewer: str | None
    model_info: dict
    reviewed_count: int = 0


class DefectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    type: str
    category: str
    confidence: float
    polygon: list


class DefectCreate(BaseModel):
    type: str
    category: str
    polygon: list
    confidence: float = 1.0


class DefectPatch(BaseModel):
    type: str | None = None
    category: str | None = None
    polygon: list | None = None


class SegmentRequest(BaseModel):
    point: list[float] | None = None
    box: list[float] | None = None


class SegmentResponse(BaseModel):
    polygon: list


class ImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    url: str
    width: int
    height: int
    status: str
    reviewed: bool
    mask_polygon: list | None
    defects: list[DefectOut]


class BatchResult(BaseModel):
    batch_name: str
    source_path: str
    images: list[ImageOut]


class BatchPatch(BaseModel):
    status: str | None = None
    reviewer: str | None = None
    name: str | None = None


class ImagePatch(BaseModel):
    reviewed: bool


class QuantityCheckPatch(BaseModel):
    name: str | None = None


class QuantityCheckIn(BaseModel):
    source_type: str = "image"
    count_mode: str = "static"
    input_summary: str = ""
    model_used: str = ""
    confidence_used: float = 0.5
    total_count: int
    per_class_counts: dict = {}
    expected_total: int | None = None
    expected_per_class: dict = {}
    inputs: list = []
    tolerance: int = 0
    verdict: str = "none"
    reviewer: str = ""
    notes: str = ""


class QuantityCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: str
    name: str = ""
    source_type: str
    count_mode: str
    input_summary: str
    model_used: str
    confidence_used: float
    total_count: int
    per_class_counts: dict
    expected_total: int | None
    expected_per_class: dict
    inputs: list
    tolerance: int
    verdict: str
    reviewer: str
    notes: str


class MeasurementItemIn(BaseModel):
    id: str
    type: str
    label: str = ""
    task_type: str | None = None
    view_type: str = "top"
    points: list[list[float]] = Field(default_factory=list)
    geometry: dict | None = None
    nominal: float | None = None
    tolerance: float | None = None
    confidence: float = 0.0


class MeasurementProcessOut(BaseModel):
    source_key: str
    source_type: str
    source_filename: str
    source_camera_id: str | None = None
    frame_url: str
    width: int
    height: int
    calibration: dict
    task_type: str = "linear_dimension"
    view_type: str = "top"
    readiness: str
    reason: str
    candidates: list
    holes: list = Field(default_factory=list)


class MeasurementRunIn(BaseModel):
    name: str
    source_key: str
    source_filename: str
    source_type: str = "image"
    source_camera_id: str | None = None
    task_type: str = "linear_dimension"
    view_type: str = "top"
    calibration: dict
    items: list[MeasurementItemIn] = []


class MeasurementRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: str
    name: str
    source_type: str
    source_filename: str
    source_camera_id: str | None
    source_url: str
    width: int
    height: int
    calibration: dict
    processing: dict
    items: list
    summary: dict
