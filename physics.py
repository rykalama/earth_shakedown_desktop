"""Pymunk simulation and explicit support-relationship tracking."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pymunk

from calculations import shake_displacement, shake_velocity
from models import PlacedPiece, Structure, TrialState


PIXELS_PER_INCH = 3.0
TABLE_Y_IN = 370.0
TABLE_HALF_WIDTH_IN = 110.0
# Support is intentionally forgiving: the graph records the intended load path,
# while these broad tolerances allow a player to start with visible gaps and let
# Pymunk settle the pieces naturally.
SUPPORT_HORIZONTAL_TOLERANCE_IN = 90.0
SUPPORT_VERTICAL_TOLERANCE_IN = 140.0
# Separation is measured from each relationship's starting relative position.
# These tolerances preserve forgiving setup gaps while catching a structure that
# actually comes apart during the test.
DISCONNECT_HORIZONTAL_DELTA_IN = 35.0
DISCONNECT_VERTICAL_DELTA_IN = 50.0


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
        self.table_shape = pymunk.Segment(self.table_body, (-TABLE_HALF_WIDTH_IN * PIXELS_PER_INCH, 0),
                                          (TABLE_HALF_WIDTH_IN * PIXELS_PER_INCH, 0), 2)
        self.table_shape.friction = 1.0
        self.space.add(self.table_body, self.table_shape)
        self.bodies: dict[int, pymunk.Body] = {}
        self.shapes: dict[int, pymunk.Shape] = {}
        self._detached_since: dict[int, float] = {}
        self._build_pieces()
        self._support_reference = self._capture_support_reference()

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
        # The calculation module returns feet and feet/second. Convert back to
        # the table's inch-based geometry at the simulation boundary.
        displacement_in = shake_displacement(elapsed_s, amplitude_in, frequency_hz) * 12.0
        velocity_in_s = shake_velocity(elapsed_s, amplitude_in, frequency_hz) * 12.0
        self.table_body.position = ((180 + displacement_in) * PIXELS_PER_INCH,
                                    TABLE_Y_IN * PIXELS_PER_INCH)
        self.table_body.velocity = (velocity_in_s * PIXELS_PER_INCH, 0.0)
        self.space.step(max(0.001, min(dt_s, 0.05)))
        return self.detect_failure(elapsed_s)

    def detect_failure(self, elapsed_s: float) -> Failure | None:
        # Report the first piece that physically leaves the table before
        # reporting support failures cascading from that piece.
        table_center_x_in = self.table_body.position.x / PIXELS_PER_INCH
        table_left_in = table_center_x_in - TABLE_HALF_WIDTH_IN
        table_right_in = table_center_x_in + TABLE_HALF_WIDTH_IN
        for piece_id, body in self.bodies.items():
            shape = self.shapes[piece_id]
            shape_left_in = shape.bb.left / PIXELS_PER_INCH
            shape_right_in = shape.bb.right / PIXELS_PER_INCH
            off_table = shape_right_in < table_left_in or shape_left_in > table_right_in
            below_table = body.position.y > (TABLE_Y_IN + 90) * PIXELS_PER_INCH
            outside_canvas = body.position.x < -30 or body.position.x > 390 * PIXELS_PER_INCH
            if off_table or below_table or outside_canvas:
                return Failure(piece_id, "piece fell off the shake table")

        for relation in self.structure.supports:
            child = self.shapes.get(relation.child_id)
            parent = self.shapes.get(relation.parent_id) if relation.parent_id is not None else None
            if child is None:
                continue
            if not self._support_is_intact(relation, child, parent):
                self._detached_since.setdefault(relation.child_id, elapsed_s)
                return Failure(relation.child_id, "required support disconnected")
            self._detached_since.pop(relation.child_id, None)

        return None

    def _capture_support_reference(self) -> dict[tuple[int, int | None], tuple[float, float]]:
        reference: dict[tuple[int, int | None], tuple[float, float]] = {}
        for relation in self.structure.supports:
            child = self.bodies.get(relation.child_id)
            if child is None:
                continue
            if relation.parent_id is None:
                parent_x, parent_y = self.table_body.position
            else:
                parent = self.bodies.get(relation.parent_id)
                if parent is None:
                    continue
                parent_x, parent_y = parent.position
            reference[(relation.child_id, relation.parent_id)] = (
                child.position.x - parent_x,
                child.position.y - parent_y,
            )
        return reference

    def _support_is_intact(self, relation, child: pymunk.Shape, parent: pymunk.Shape | None) -> bool:
        child_x, child_y = child.body.position
        if parent is None:
            parent_x, parent_y = self.table_body.position
        else:
            parent_x, parent_y = parent.body.position
        horizontal_distance_in = abs(child_x - parent_x) / PIXELS_PER_INCH
        vertical_distance_in = abs(child_y - parent_y) / PIXELS_PER_INCH
        if (horizontal_distance_in > SUPPORT_HORIZONTAL_TOLERANCE_IN
                or vertical_distance_in > SUPPORT_VERTICAL_TOLERANCE_IN):
            return False

        reference = self._support_reference.get((relation.child_id, relation.parent_id))
        if reference is None:
            return False
        reference_dx, reference_dy = reference
        current_dx = child_x - parent_x
        current_dy = child_y - parent_y
        return (
            abs(current_dx - reference_dx) / PIXELS_PER_INCH <= DISCONNECT_HORIZONTAL_DELTA_IN
            and abs(current_dy - reference_dy) / PIXELS_PER_INCH <= DISCONNECT_VERTICAL_DELTA_IN
        )

    def positions_in_inches(self) -> dict[int, tuple[float, float, float]]:
        return {
            piece_id: (body.position.x / PIXELS_PER_INCH,
                       body.position.y / PIXELS_PER_INCH,
                       math.degrees(body.angle))
            for piece_id, body in self.bodies.items()
        }

