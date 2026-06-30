import os

import cv2


def crop_objects(frame, detections, out_dir, scale=1.0, start_index=0, pad_frac=0.05):
    os.makedirs(out_dir, exist_ok=True)
    h, w = frame.shape[:2]
    files = []
    idx = start_index
    for d in detections:
        x1 = d.x1 * scale
        y1 = d.y1 * scale
        x2 = d.x2 * scale
        y2 = d.y2 * scale
        if x2 <= x1 or y2 <= y1:
            continue
        px = (x2 - x1) * pad_frac
        py = (y2 - y1) * pad_frac
        cx1 = max(0, int(round(x1 - px)))
        cy1 = max(0, int(round(y1 - py)))
        cx2 = min(w, int(round(x2 + px)))
        cy2 = min(h, int(round(y2 + py)))
        if cx2 <= cx1 or cy2 <= cy1:
            continue
        crop = frame[cy1:cy2, cx1:cx2]
        filename = f"obj_{idx:03d}.png"
        cv2.imwrite(os.path.join(out_dir, filename), crop)
        files.append(filename)
        idx += 1
    return files
