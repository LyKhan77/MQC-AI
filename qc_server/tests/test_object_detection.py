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


def test_detect_forwards_selected_device(monkeypatch):
    captured = {}

    class _Results:
        boxes = None
        names = {}

    def fake_model(frame, **kwargs):
        captured.update(kwargs)
        return [_Results()]

    monkeypatch.setattr(object_detection, "get_model", lambda *_: fake_model)
    object_detection.detect("frame", 0.5, "m.pt", device="1")

    assert captured["device"] == "1"


def test_detect_prompts_none_uses_shared_model(monkeypatch):
    used = []
    model = _Model()
    monkeypatch.setattr(object_detection, "get_model", lambda _: used.append("plain") or model)
    monkeypatch.setattr(
        object_detection,
        "get_prompt_model",
        lambda _: (_ for _ in ()).throw(AssertionError("prompt model used")),
        raising=False,
    )

    object_detection.detect(object(), 0.2, "m.pt", prompts=None)

    assert used == ["plain"]


def test_detect_prompt_sets_classes_only_when_changed(monkeypatch):
    calls = []

    class _PromptModel(_Model):
        def set_classes(self, prompts):
            calls.append(list(prompts))

    model = _PromptModel()
    monkeypatch.setattr(object_detection, "get_prompt_model", lambda _: model, raising=False)
    monkeypatch.setattr(object_detection, "_pmodel_classes", None, raising=False)

    object_detection.detect(object(), 0.2, "m.pt", prompts=["bolt", "nut"])
    object_detection.detect(object(), 0.2, "m.pt", prompts=["bolt", "nut"])
    object_detection.detect(object(), 0.2, "m.pt", prompts=["bolt"])

    assert calls == [["bolt", "nut"], ["bolt"]]


def test_detect_prompt_rejects_models_without_class_prompts(monkeypatch):
    class _BadPromptModel(_Model):
        def set_classes(self, prompts):
            raise AttributeError("nope")

    monkeypatch.setattr(object_detection, "get_prompt_model", lambda _: _BadPromptModel(), raising=False)
    monkeypatch.setattr(object_detection, "_pmodel_classes", None, raising=False)

    try:
        object_detection.detect(object(), 0.2, "m.pt", prompts=["bolt"])
    except ValueError as exc:
        assert str(exc) == "model does not support class prompts"
    else:
        raise AssertionError("expected ValueError")
