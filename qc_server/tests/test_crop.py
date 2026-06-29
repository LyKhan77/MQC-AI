import os

import numpy as np

from app.services.crop import crop_objects
from app.services.object_detection import Detection


def test_crop_objects_writes_one_file_per_detection(tmp_path):
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    dets = [Detection(10, 10, 30, 30, "obj", 0.9), Detection(40, 40, 80, 80, "obj", 0.8)]
    files = crop_objects(frame, dets, str(tmp_path))
    assert files == ["obj_000.jpg", "obj_001.jpg"]
    for f in files:
        assert os.path.isfile(tmp_path / f)


def test_crop_objects_scales_coords(tmp_path):
    # 50x50 detection coords on a downscaled frame, scale=2 -> crop a 100x100 region from a 200x200 original
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    dets = [Detection(0, 0, 50, 50, "obj", 0.9)]
    files = crop_objects(frame, dets, str(tmp_path), scale=2.0)
    import cv2
    img = cv2.imread(str(tmp_path / files[0]))
    assert img.shape[0] == 100 and img.shape[1] == 100


def test_crop_objects_start_index_and_skip_empty(tmp_path):
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    dets = [Detection(5, 5, 5, 5, "obj", 0.9), Detection(10, 10, 40, 40, "obj", 0.9)]
    files = crop_objects(frame, dets, str(tmp_path), start_index=7)
    # zero-area box skipped, numbering continues from start_index for kept boxes
    assert files == ["obj_007.jpg"]
