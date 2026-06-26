from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class Detection:
    type: str
    category: str
    confidence: float
    polygon: list[list[int]]


@dataclass
class DefectClassSpec:
    name: str
    category: str
    enabled: bool = True


@runtime_checkable
class DefectStrategy(Protocol):
    name: str

    def detect(self, image_path: str, width: int, height: int,
               defect_classes: list[DefectClassSpec], params: dict) -> list[Detection]:
        ...


STRATEGIES: dict[str, DefectStrategy] = {}


def register(strategy: DefectStrategy) -> None:
    STRATEGIES[strategy.name] = strategy


def get_strategy(name: str) -> DefectStrategy:
    return STRATEGIES.get(name) or STRATEGIES["mock"]
