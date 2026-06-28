from app.services.counting import count_single, update_tracking
from app.services.inference import Detection


def _det(track_id=None):
    return Detection(x1=0, y1=0, x2=1, y2=1, label="x", confidence=0.9, track_id=track_id)


def test_count_single_is_instantaneous():
    assert count_single([_det(), _det()]) == 2
    assert count_single([]) == 0


def test_update_tracking_accumulates_unique_ids():
    seen = set()
    assert update_tracking(seen, [_det(1), _det(2)]) == 2
    assert update_tracking(seen, [_det(2), _det(3)]) == 3
    assert update_tracking(seen, [_det(None)]) == 3
