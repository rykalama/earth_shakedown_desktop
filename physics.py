"""Pymunk simulation and explicit support-relationship tracking."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pymunk

from calculations import shake_displacement, shake_velocity
from models import PlacedPiece, Structure, TrialState


PIXELS_PER_INCH = 3.0
TABLE_Y_IN = 370.0


@dataclass
class Failure:
    piece_id: int
    reason: str


class ShakeSimulation:
    def __init__(self, structure: Structure):
        self.structure = structure
        self.space = pymunk.Space()
        self.space.gravity = (0.0, 32.174 * PIXELS_PER_INCH)
        self.table_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.table_body.position = (180 * PIXELS_PER_INCH, TABLE_Y_IN * PIXELS_PER_INCH)
        self.table_shape = pymunk.Segment(self.table_body, (-110 * PIXELS_PER_INCH, 0),
                                          (110 * PIXELS_PER_INCH, 0), 2)
        self.table_shape.friction = 1.0
        self.space.add(self.table_body, self.table_shape)
        self.bodies: dict[int, pymunk.Body] = {}
        self.shapes: dict[int, pymunk.Shape] = {}
        self._detached_since: dict[int, float] = {}
        self._build_pieces()

    def _build_pieces(self) -> None:
        for piece in self.structure.pieces:
            definition = piece.definition
            mass = max(0.1, definition.mass_lb)
            moment = pymunk.moment_for_box(mass, (
                definition.width_in * PIXELS_PER_INCH,
                definition.height_in * PIXELS_PER_INCH,
            ))
            body = pymunk.Body(mass, moment)
            body.position = (piece.x_in * PIXELS_PER_INCH, piece.y_in * PIXELS_PER_INCH)
            body.angle = math.radians(piece.angle_deg)
            shape = pymunk.Poly.create_box(
                body,
                (definition.width_in * PIXELS_PER_INCH,
                 definition.height_in * PIXELS_PER_INCH),
            )
            shape.friction = 0.85
            shape.elasticity = 0.05
            shape.piece_id = piece.piece_id
            self.space.add(body, shape)
            self.bodies[piece.piece_id] = body
            self.shapes[piece.piece_id] = shape

    def reset(self) -> None:
        for body in self.bodies.values():
            body.velocity = (0, 0)
            body.angular_velocity = 0
        self._detached_since.clear()

    def step(self, elapsed_s: float, dt_s: float, amplitude_in: float, frequency_hz: float) -> Failure | None:
        displacement = shake_displacement(elapsed_s, amplitude_in, frequency_hz)
        velocity = shake_velocity(elapsed_s, amplitude_in, frequency_hz)
        self.table_body.position = ((180 + displacement) * PIXELS_PER_INCH,
                                    TABLE_Y_IN * PIXELS_PER_INCH)
        self.table_body.velocity = (velocity * PIXELS_PER_INCH, 0.0)
        self.space.step(max(0.001, min(dt_s, 0.05)))
        return self.detect_failure(elapsed_s)

    def detect_failure(self, elapsed_s: float) -> Failure | None:
        for relation in self.structure.supports:
            if relation.parent_id is None:
                continue
            child = self.shapes.get(relation.child_id)
            parent = self.shapes.get(relation.parent_id)
            if child is None or parent is None:
                continue
            if not self._has_geometric_support(child, parent):
                self._detached_since.setdefault(relation.child_id, elapsed_s)
                return Failure(relation.child_id, "required support disconnected")
            self._detached_since.pop(relation.child_id, None)

        for piece_id, body in self.bodies.items():
            x, y = body.position
            if y > (TABLE_Y_IN + 90) * PIXELS_PER_INCH or x < -30 or x > 390 * PIXELS_PER_INCH:
                return Failure(piece_id, "crossed the simulation boundary")
        return None

    @staticmethod
    def _has_geometric_support(child: pymunk.Shape, parent: pymunk.Shape) -> bool:
        child_box = child.bb
        parent_box = parent.bb
        horizontal_overlap = min(child_box.right, parent_box.right) - max(child_box.left, parent_box.left)
        # The app's canvas uses increasing y downward, while Pymunk's BB still
        # exposes bottom/top as numeric min/max values. The child's lower edge
        # is therefore its numeric top, and the parent's upper edge is bottom.
        vertical_gap = child_box.top - parent_box.bottom
        return horizontal_overlap > 1.0 and vertical_gap <= 18.0 and vertical_gap >= -45.0

    def positions_in_inches(self) -> dict[int, tuple[float, float, float]]:
        return {
            piece_id: (body.position.x / PIXELS_PER_INCH,
                       body.position.y / PIXELS_PER_INCH,
                       math.degrees(body.angle))
            for piece_id, body in self.bodies.items()
        }

