import pytest

from app.services.inference import sam3
from app.services.inference.base import DefectClassSpec


def test_simplify_polygon_reduces_collinear_and_clamps():
    pts = [[10, 10], [25, 10], [40, 10], [40, 40], [10, 40]]
    out = sam3.simplify_polygon(pts, epsilon=2.0, width=100, height=100)
    assert out == [[10, 10], [40, 10], [40, 40], [10, 40]]
    assert all(isinstance(x, int) and isinstance(y, int) for x, y in out)


def test_simplify_polygon_clamps_out_of_bounds():
    pts = [[-5, -5], [200, -5], [200, 200], [-5, 200]]
    out = sam3.simplify_polygon(pts, epsilon=2.0, width=100, height=80)
    assert out == [[0, 0], [100, 0], [100, 80], [0, 80]]


def test_simplify_polygon_drops_degenerate():
    assert sam3.simplify_polygon([[1, 1], [2, 2]], epsilon=2.0, width=10, height=10) == []


class _FakeMasks:
    def __init__(self, xy):
        self.xy = xy


class _FakeBoxes:
    def __init__(self, conf):
        self.conf = conf


class _FakeResult:
    def __init__(self, xy, conf):
        self.masks = _FakeMasks(xy)
        self.boxes = _FakeBoxes(conf)


class _FakePredictor:
    def __init__(self, mapping):
        self.mapping = mapping
        self.image = None

    def set_image(self, path):
        self.image = path

    def __call__(self, text):
        return self.mapping.get(text[0], [])


def test_detect_maps_filters_and_simplifies(monkeypatch):
    square = [[10, 10], [25, 10], [40, 10], [40, 40], [10, 40]]
    mapping = {
        "scratch": [_FakeResult([square], [0.91])],
        "dent": [_FakeResult([[[1, 1], [1, 9], [9, 9], [9, 1]]], [0.2])],
    }
    fake = _FakePredictor(mapping)
    monkeypatch.setattr(sam3, "get_predictor", lambda _: fake)

    specs = [
        DefectClassSpec("scratch", "coating", True),
        DefectClassSpec("dent", "welding", True),
        DefectClassSpec("disabled", "coating", False),
    ]
    dets = sam3.Sam3Strategy().detect(
        "img.jpg", 100, 100, specs,
        {"qc_model_path": "sam3.pt", "confidence_threshold": 0.5},
    )

    assert fake.image == "img.jpg"
    assert len(dets) == 1
    assert dets[0].type == "scratch"
    assert dets[0].category == "coating"
    assert dets[0].confidence == 0.91
    assert dets[0].polygon == [[10, 10], [40, 10], [40, 40], [10, 40]]


def test_detect_requires_qc_model_path():
    with pytest.raises(ValueError):
        sam3.Sam3Strategy().detect("img.jpg", 10, 10, [], {"confidence_threshold": 0.5})
