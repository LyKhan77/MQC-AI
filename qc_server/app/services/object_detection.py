from dataclasses import dataclass

from ..config import settings

_model = None


@dataclass
class Detection:
    x1: int
    y1: int
    x2: int
    y2: int
    label: str
    confidence: float
    track_id: int | None = None


def serialize_detections(detections):
    return [
        {
            "box": [d.x1, d.y1, d.x2, d.y2],
            "label": d.label,
            "confidence": round(d.confidence, 3),
            "track_id": d.track_id,
        }
        for d in detections
    ]


def load_model():
    global _model
    if _model is None:
        if not settings.model_path:
            raise RuntimeError("MQC_MODEL_PATH is not configured")
        from ultralytics import YOLO  # lazy, server-only

        _model = YOLO(settings.model_path)
    return _model


def detect(frame, conf_threshold):
    # Smoke-verified on the GPU server. Unit tests avoid ML deps.
    import supervision as sv  # lazy, server-only

    model = load_model()
    results = model(frame, verbose=False)[0]
    sv_det = sv.Detections.from_ultralytics(results)
    if sv_det.confidence is not None:
        sv_det = sv_det[sv_det.confidence >= conf_threshold]

    names = results.names
    out = []
    for i in range(len(sv_det)):
        x1, y1, x2, y2 = sv_det.xyxy[i]
        class_id = int(sv_det.class_id[i]) if sv_det.class_id is not None else -1
        out.append(
            Detection(
                x1=int(x1),
                y1=int(y1),
                x2=int(x2),
                y2=int(y2),
                label=str(names.get(class_id, class_id)),
                confidence=float(sv_det.confidence[i]) if sv_det.confidence is not None else 1.0,
            )
        )
    return out
