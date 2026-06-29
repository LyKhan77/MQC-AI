def apply_tracker(tracker, detections):
    # Smoke-verified on GPU server against installed supervision version.
    import numpy as np
    import supervision as sv

    if not detections:
        return detections
    xyxy = np.array([[d.x1, d.y1, d.x2, d.y2] for d in detections], dtype=float)
    conf = np.array([d.confidence for d in detections], dtype=float)
    class_id = np.zeros(len(detections), dtype=int)
    sv_det = sv.Detections(xyxy=xyxy, confidence=conf, class_id=class_id)
    tracked = tracker.update_with_detections(sv_det)
    for i in range(len(tracked)):
        detections[i].track_id = (
            int(tracked.tracker_id[i]) if tracked.tracker_id is not None else None
        )
    return detections
