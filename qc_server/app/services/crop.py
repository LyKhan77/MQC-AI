import os

import cv2


def crop_objects(frame, detections, out_dir, scale=1.0, start_index=0):
    os.makedirs(out_dir, exist_ok=True)
    h, w = frame.shape[:2]
    files = []
    idx = start_index
    for d in detections:
        x1 = max(0, min(w, int(d.x1 * scale)))
        y1 = max(0, min(h, int(d.y1 * scale)))
        x2 = max(0, min(w, int(d.x2 * scale)))
        y2 = max(0, min(h, int(d.y2 * scale)))
        if x2 <= x1 or y2 <= y1:
            continue
        crop = frame[y1:y2, x1:x2]
        filename = f"obj_{idx:03d}.jpg"
        cv2.imwrite(os.path.join(out_dir, filename), crop)
        files.append(filename)
        idx += 1
    return files
