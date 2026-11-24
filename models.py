"""Shared domain models for Earthquake Shake-Down."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TrialState(str, Enum):
    EDITING = "Editing"
    RUNNING = "Running"
    PAUSED = "Paused"
    CHECKPOINT = "10-second checkpoint"
    FAILED = "Failed"
    COMPLETE = "Complete"


@dataclass(frozen=True)
class PieceDefinition:
    key: str
    name: str
    category: str
    width_in: float
    height_in: float
    mass_lb: float
    price: float
    shape: str
    material: str
    color: str
    price_source: str
    price_checked: str


@dataclass
class PlacedPiece:
    piece_id: int
    definition: PieceDefinition
    x_in: float
    y_in: float
    angle_deg: float = 0.0


@dataclass(frozen=True)
class SupportRelation:
    child_id: int
    parent_id: Optional[int]
    relation_type: str = "contact"


@dataclass(frozen=True)
class Weld:
    first_id: int
    second_id: int


@dataclass
class TrialRecord:
    amplitude_in: float
    frequency_hz: float
    max_speed_ft_s: float
    max_acceleration_ft_s2: float
    checkpoint_reached: bool
    survival_time_s: float
    failed_piece_id: Optional[int] = None
    failure_reason: Optional[str] = None


@dataclass
class Structure:
    pieces: list[PlacedPiece] = field(default_factory=list)
    supports: list[SupportRelation] = field(default_factory=list)
    welds: list[Weld] = field(default_factory=list)

    def total_cost(self) -> float:
        return sum(piece.definition.price for piece in self.pieces)

