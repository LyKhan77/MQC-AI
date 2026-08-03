import os
from dataclasses import dataclass

from ..config import settings

_models = {}
_prompt_models = {}
_prompt_classes = {}


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


def resolve_model_path(setting):
    name = getattr(setting, "active_model", "") or ""
    if not name:
        return None
    path = os.path.join(settings.models_dir, name)
    return path if os.path.isfile(path) else None


def resolve_named_model_path(name):
    name = name or ""
    if not name:
        return None
    path = os.path.join(settings.models_dir, name)
    return path if os.path.isfile(path) else None


def get_model(model_path, device="auto"):
    cache_key = (model_path, device)
    if cache_key not in _models:
        from ultralytics import YOLO  # lazy, server-only

        _models[cache_key] = YOLO(model_path)
    return _models[cache_key]


def get_prompt_model(model_path, device="auto"):
    cache_key = (model_path, device)
    if cache_key not in _prompt_models:
        from ultralytics import YOLOE  # lazy, server-only

        _prompt_models[cache_key] = YOLOE(model_path)
        _prompt_classes.pop(cache_key, None)
    return _prompt_models[cache_key]


def _detections_from_result(results):
    boxes = results.boxes
    if boxes is None:
        return []
    names = results.names

    xyxy = boxes.xyxy.cpu().numpy()
    class_ids = boxes.cls.cpu().numpy().astype(int)
    confidences = boxes.conf.cpu().numpy()

    out = []
    for i in range(len(boxes)):
        x1, y1, x2, y2 = xyxy[i]
        class_id = int(class_ids[i])
        out.append(
            Detection(
                x1=int(x1),
                y1=int(y1),
                x2=int(x2),
                y2=int(y2),
                label=str(names.get(class_id, class_id)),
                confidence=float(confidences[i]),
            )
        )
    return out


def detect(
    frame,
    conf_threshold,
    model_path,
    iou=None,
    agnostic_nms=False,
    prompts=None,
    device="auto",
):
    # Smoke-verified on the GPU server. Unit tests avoid ML deps.
    if prompts is None:
        model = get_model(model_path) if device == "auto" else get_model(model_path, device)
    else:
        model = get_prompt_model(model_path) if device == "auto" else get_prompt_model(model_path, device)
        prompt_list = list(prompts)
        cache_key = (model_path, device)
        if _prompt_classes.get(cache_key) != (id(model), prompt_list):
            try:
                model.set_classes(prompt_list)
            except Exception as exc:
                raise ValueError("model does not support class prompts") from exc
            _prompt_classes[cache_key] = (id(model), prompt_list)

    kwargs = {"conf": conf_threshold, "verbose": False, "agnostic_nms": agnostic_nms}
    if iou is not None:
        kwargs["iou"] = iou
    if device != "auto":
        kwargs["device"] = device
    results = model(frame, **kwargs)[0]
    return _detections_from_result(results)
