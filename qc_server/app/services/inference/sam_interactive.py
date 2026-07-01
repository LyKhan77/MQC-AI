import os

from .sam3 import POLYGON_EPSILON, simplify_polygon

_model = None
_model_path = None


def get_model(model_path):
    global _model, _model_path
    if _model is None or _model_path != model_path:
        from ultralytics import SAM

        _model = SAM(model_path)
        _model_path = model_path
    return _model


def _best_index(boxes):
    confs = getattr(boxes, "conf", None) if boxes is not None else None
    if confs is None:
        return 0
    values = [float(c) for c in confs]
    if not values:
        return 0
    return max(range(len(values)), key=values.__getitem__)


def segment(image_path, width, height, point=None, box=None, model_path=""):
    if not model_path or not os.path.exists(model_path):
        raise ValueError("No QC model selected (Settings -> QC / Segmentation Model)")

    model = get_model(model_path)
    if point is not None:
        results = model(image_path, points=[[point[0], point[1]]], labels=[1],
                        verbose=False, save=False)
    else:
        results = model(image_path, bboxes=[[box[0], box[1], box[2], box[3]]],
                        verbose=False, save=False)

    if not results:
        return []
    res = results[0]
    masks = getattr(res, "masks", None)
    polys = getattr(masks, "xy", []) if masks is not None else []
    if not polys:
        return []
    index = min(_best_index(getattr(res, "boxes", None)), len(polys) - 1)
    return simplify_polygon(polys[index], POLYGON_EPSILON, width, height)
