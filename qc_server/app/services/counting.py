def count_single(detections) -> int:
    return len(detections)


def update_tracking(seen_ids: set, detections) -> int:
    for d in detections:
        if d.track_id is not None:
            seen_ids.add(d.track_id)
    return len(seen_ids)
