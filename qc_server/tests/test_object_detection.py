from app.services import object_detection


class _Array:
    def __init__(self, value):
        self._value = value

    def cpu(self):
        return self

    def numpy(self):
        return self._value


class _Boxes:
    def __init__(self):
        self.xyxy = _Array([[1.2, 2.8, 10.9, 20.1]])
        self.cls = _Array(_ClassIds([0]))
        self.conf = _Array([0.1234])

    def __len__(self):
        return 1


class _ClassIds(list):
    def astype(self, _type):
        return [int(v) for v in self]


class _Result:
    boxes = _Boxes()
    names = {0: "pcb"}


class _Model:
    def __init__(self):
        self.conf = None

    def __call__(self, frame, conf, verbose, **kwargs):
        self.conf = conf
        return [_Result()]


def test_detect_passes_conf_and_parses_ultralytics_boxes(monkeypatch):
    model = _Model()
    monkeypatch.setattr(object_detection, "get_model", lambda _: model)

    detections = object_detection.detect(frame=object(), conf_threshold=0.1, model_path="m.pt")

    assert model.conf == 0.1
    assert detections == [object_detection.Detection(1, 2, 10, 20, "pcb", 0.1234)]


def test_detect_forwards_nms_params(monkeypatch):
    captured = {}

    class _Results:
        boxes = None
        names = {}

    def fake_model(frame, **kwargs):
        captured.update(kwargs)
        return [_Results()]

    monkeypatch.setattr(object_detection, "get_model", lambda _: fake_model)
    out = object_detection.detect("frame", 0.5, "m.pt", iou=0.45, agnostic_nms=True)

    assert out == []
    assert captured["conf"] == 0.5
    assert captured["iou"] == 0.45
    assert captured["agnostic_nms"] is True
