from app.services.inference.base import DefectClassSpec, get_strategy
import app.services.inference.mock  # noqa: F401  (registers "mock")

SPECS = [DefectClassSpec("porosity", "welding"), DefectClassSpec("scratch", "coating")]


def test_mock_is_deterministic():
    s = get_strategy("mock")
    a = s.detect("/x/weld_0001.jpg", 1280, 960, SPECS, {})
    b = s.detect("/x/weld_0001.jpg", 1280, 960, SPECS, {})
    assert [d.__dict__ for d in a] == [d.__dict__ for d in b]


def test_mock_clean_filename_has_no_defects():
    s = get_strategy("mock")
    assert s.detect("/x/clean_part.jpg", 1280, 960, SPECS, {}) == []


def test_mock_defect_shape_within_bounds():
    s = get_strategy("mock")
    dets = s.detect("/x/weld_0007.jpg", 1280, 960, SPECS, {})
    for d in dets:
        assert d.category in {"welding", "coating"}
        assert 0.0 <= d.confidence <= 1.0
        assert len(d.polygon) >= 3
        for x, y in d.polygon:
            assert 0 <= x <= 1280 and 0 <= y <= 960


def test_unknown_strategy_falls_back_to_mock():
    assert get_strategy("does-not-exist").name == "mock"
