from collections import Counter


def per_class_counts(detections):
    """Map each detection label to its occurrence count."""
    return dict(Counter(d.label for d in detections))
