import os

from .sam3 import POLYGON_EPSILON, simplify_polygon

_models = {}


def get_model(model_path, device="auto"):
    cache_key = (model_path, device)
    if cache_key not in _models:
        from ultralytics import SAM

        _models[cache_key] = SAM(model_path)
    return _models[cache_key]


def _best_index(boxes):
    confs = getattr(boxes, "conf", None) if boxes is not None else None
    if confs is None:
        return 0
    values = [float(c) for c in confs]
    if not values:
        return 0
    return max(range(len(values)), key=values.__getitem__)


def segment(image_path, width, height, point=None, box=None, model_path="", device="auto"):
    if not model_path or not os.path.exists(model_path):
        raise ValueError("No QC model selected (Settings -> QC / Segmentation Model)")

    model = get_model(model_path) if device == "auto" else get_model(model_path, device)
    device_kwargs = {} if device == "auto" else {"device": device}
    if point is not None:
        results = model(image_path, points=[[point[0], point[1]]], labels=[1],
                        verbose=False, save=False, **device_kwargs)
    else:
        results = model(image_path, bboxes=[[box[0], box[1], box[2], box[3]]],
                        verbose=False, save=False, **device_kwargs)

    if not results:
        return []
    res = results[0]
    masks = getattr(res, "masks", None)
    polys = getattr(masks, "xy", []) if masks is not None else []
    if not polys:
        return []
    index = min(_best_index(getattr(res, "boxes", None)), len(polys) - 1)
    return simplify_polygon(polys[index], POLYGON_EPSILON, width, height)
