import hashlib
import math
import os
import random

from .base import Detection, DefectClassSpec, register


class MockStrategy:
    name = "mock"

    def detect(self, image_path: str, width: int, height: int,
               defect_classes: list[DefectClassSpec], params: dict) -> list[Detection]:
        filename = os.path.basename(image_path)
        if "clean" in filename.lower():
            return []

        seed = int(hashlib.md5(filename.encode()).hexdigest(), 16)
        rng = random.Random(seed)
        count = rng.choice([0, 1, 1, 2])
        if count == 0:
            return []

        usable = [c for c in defect_classes if c.enabled] or defect_classes
        if not usable:
            return []

        detections: list[Detection] = []
        for _ in range(count):
            cls = rng.choice(usable)
            cx = rng.randint(int(width * 0.2), int(width * 0.8))
            cy = rng.randint(int(height * 0.2), int(height * 0.8))
            radius = rng.randint(30, 80)
            polygon = [
                [
                    max(0, min(width, cx + int(radius * math.cos(k * math.pi / 3)))),
                    max(0, min(height, cy + int(radius * math.sin(k * math.pi / 3)))),
                ]
                for k in range(6)
            ]
            detections.append(Detection(
                type=cls.name,
                category=cls.category,
                confidence=round(rng.uniform(0.6, 0.98), 2),
                polygon=polygon,
            ))
        return detections


register(MockStrategy())
