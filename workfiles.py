"""Portable JSON serialization for editable Earthquake Shake-Down work."""

from __future__ import annotations

from typing import Any

from catalog import CATALOG
from models import PlacedPiece, Structure, SupportRelation, Weld


WORK_FILE_VERSION = 1


def structure_to_dict(structure: Structure) -> dict[str, Any]:
    return {
        "version": WORK_FILE_VERSION,
        "pieces": [
            {
                "piece_id": piece.piece_id,
                "type": piece.definition.key,
                "x_in": piece.x_in,
                "y_in": piece.y_in,
                "angle_deg": piece.angle_deg,
            }
            for piece in structure.pieces
        ],
        "supports": [
            {
                "child_id": relation.child_id,
                "parent_id": relation.parent_id,
                "relation_type": relation.relation_type,
            }
            for relation in structure.supports
        ],
        "welds": [
            {"first_id": weld.first_id, "second_id": weld.second_id}
            for weld in structure.welds
        ],
    }


def structure_from_dict(data: dict[str, Any]) -> Structure:
    if not isinstance(data, dict) or data.get("version") != WORK_FILE_VERSION:
        raise ValueError("This is not a supported Earthquake Shake-Down work file.")

    pieces: list[PlacedPiece] = []
    for raw_piece in data.get("pieces", []):
        piece_type = raw_piece["type"]
        if piece_type not in CATALOG:
            raise ValueError(f"Unknown catalog piece type: {piece_type}")
        pieces.append(PlacedPiece(
            int(raw_piece["piece_id"]),
            CATALOG[piece_type],
            float(raw_piece["x_in"]),
            float(raw_piece["y_in"]),
            float(raw_piece.get("angle_deg", 0.0)),
        ))

    supports = [
        SupportRelation(
            int(raw_relation["child_id"]),
            None if raw_relation.get("parent_id") is None else int(raw_relation["parent_id"]),
            str(raw_relation.get("relation_type", "contact")),
        )
        for raw_relation in data.get("supports", [])
    ]
    welds = [
        Weld(int(raw_weld["first_id"]), int(raw_weld["second_id"]))
        for raw_weld in data.get("welds", [])
    ]
    return Structure(pieces, supports, welds)

