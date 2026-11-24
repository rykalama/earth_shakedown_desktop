"""Repeatable educational piece catalog and default building layout."""

from __future__ import annotations

from datetime import date

from models import PieceDefinition, PlacedPiece, Structure, SupportRelation


CHECKED = date(2026, 11, 24).isoformat()

CATALOG: dict[str, PieceDefinition] = {
    "foundation": PieceDefinition(
        "foundation", "Foundation", "Foundation", 72, 8, 180, 48.00,
        "rectangle", "Concrete", "#8b949e", "Representative retail estimate", CHECKED,
    ),
    "floor": PieceDefinition(
        "floor", "Floor deck", "Floor", 60, 6, 90, 32.00,
        "rectangle", "Wood", "#b77945", "Representative retail estimate", CHECKED,
    ),
    "column": PieceDefinition(
        "column", "Column", "Column", 6, 48, 42, 18.00,
        "rectangle", "Steel", "#5b8fb9", "Representative retail estimate", CHECKED,
    ),
    "beam": PieceDefinition(
        "beam", "Beam", "Beam", 54, 5, 36, 24.00,
        "rectangle", "Wood", "#a56538", "Representative retail estimate", CHECKED,
    ),
    "brace": PieceDefinition(
        "brace", "Diagonal brace", "Brace", 52, 4, 24, 16.00,
        "diagonal", "Steel", "#e0b44c", "Representative retail estimate", CHECKED,
    ),
    "roof": PieceDefinition(
        "roof", "Roof panel", "Roof", 64, 5, 55, 29.00,
        "rectangle", "Metal", "#704c8f", "Representative retail estimate", CHECKED,
    ),
}


def default_structure() -> Structure:
    """Return a building-like starting arrangement and its support graph."""
    pieces = [
        PlacedPiece(1, CATALOG["foundation"], 180, 330),
        PlacedPiece(2, CATALOG["column"], 160, 302),
        PlacedPiece(3, CATALOG["column"], 200, 302),
        PlacedPiece(4, CATALOG["floor"], 180, 270),
        PlacedPiece(5, CATALOG["beam"], 180, 255),
        PlacedPiece(6, CATALOG["brace"], 180, 253, -28),
        PlacedPiece(7, CATALOG["brace"], 180, 253, 28),
        PlacedPiece(8, CATALOG["roof"], 180, 237),
    ]
    supports = [
        SupportRelation(1, None, "table"),
        SupportRelation(2, 1), SupportRelation(3, 1),
        SupportRelation(4, 2), SupportRelation(4, 3),
        SupportRelation(5, 4), SupportRelation(6, 4),
        SupportRelation(7, 4), SupportRelation(8, 5),
    ]
    return Structure(pieces, supports)

