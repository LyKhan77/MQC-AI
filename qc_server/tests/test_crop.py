import os

import cv2
import numpy as np

from app.services.crop import crop_objects
from app.services.object_detection import Detection


def test_crop_objects_writes_png_per_detection(tmp_path):
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    dets = [Detection(10, 10, 30, 30, "obj", 0.9), Detection(40, 40, 80, 80, "obj", 0.8)]
    files = crop_objects(frame, dets, str(tmp_path))
    assert files == ["obj_000.png", "obj_001.png"]
    for f in files:
        assert os.path.isfile(tmp_path / f)


def test_crop_objects_scales_and_pads(tmp_path):
    # centered 50x50 box on a downscaled frame, scale=2 -> 100x100 region on a 200x200 original
    # + 8% padding (8px each side) -> 116x116
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    dets = [Detection(25, 25, 75, 75, "obj", 0.9)]
    files = crop_objects(frame, dets, str(tmp_path), scale=2.0, pad_frac=0.08)
    img = cv2.imread(str(tmp_path / files[0]))
    assert img.shape[0] == 116 and img.shape[1] == 116


def test_crop_objects_padding_clamps_to_frame(tmp_path):
    # box at the top-left corner -> padding cannot go negative
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    dets = [Detection(0, 0, 20, 20, "obj", 0.9)]
    files = crop_objects(frame, dets, str(tmp_path), pad_frac=0.08)
    img = cv2.imread(str(tmp_path / files[0]))
    # 0..round(20 + 20*0.08=21.6) => width/height 22, top-left clamped at 0
    assert img.shape[0] == 22 and img.shape[1] == 22


def test_crop_objects_start_index_and_skip_empty(tmp_path):
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    dets = [Detection(5, 5, 5, 5, "obj", 0.9), Detection(10, 10, 40, 40, "obj", 0.9)]
    files = crop_objects(frame, dets, str(tmp_path), start_index=7)
    assert files == ["obj_007.png"]
